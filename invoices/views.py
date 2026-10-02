"""
Invoice API Views
File: invoices/views.py
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse

from decimal import Decimal
from io import BytesIO

# ReportLab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.units import mm

from .models import Invoice, InvoiceItem
from orders.models import Order

from .serializers import (
    InvoiceSerializer,
    InvoiceCreateSerializer,
    InvoiceStatusUpdateSerializer,
    InvoiceListSerializer,
    InvoicePaymentSerializer,
    InvoiceCancelSerializer
)


class InvoiceViewSet(viewsets.ModelViewSet):

    queryset = Invoice.objects.all()

    serializer_class = InvoiceSerializer

    permission_classes = [IsAuthenticated]

    lookup_field = 'id'

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]

    filterset_fields = [
        'status',
        'payment_method',
        'user'
    ]

    search_fields = [
        'invoice_number',
        'transaction_id',
        'user__first_name'
    ]

    ordering_fields = [
        'issued_date',
        'total_amount',
        'status'
    ]

    ordering = ['-issued_date']

    # ---------------------------------------------------------
    # QUERYSET
    # ---------------------------------------------------------

    def get_queryset(self):

        queryset = Invoice.objects.all()

        # Staff can see all invoices
        if self.request.user.is_staff:
            return queryset

        # Normal users can see only their own invoices
        return queryset.filter(user=self.request.user)

    # ---------------------------------------------------------
    # SERIALIZER
    # ---------------------------------------------------------

    def get_serializer_class(self):

        if self.action == 'create':
            return InvoiceCreateSerializer

        elif self.action == 'update_status':
            return InvoiceStatusUpdateSerializer

        elif self.action == 'list':
            return InvoiceListSerializer

        elif self.action == 'mark_paid':
            return InvoicePaymentSerializer

        elif self.action == 'cancel':
            return InvoiceCancelSerializer

        return InvoiceSerializer

    # ---------------------------------------------------------
    # CREATE INVOICE
    # ---------------------------------------------------------

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        order = serializer.validated_data['order_id']

        due_date = serializer.validated_data.get('due_date')

        notes = serializer.validated_data.get('notes', '')

        invoice = self.create_invoice_from_order(
            order=order,
            due_date=due_date,
            notes=notes,
            user=request.user
        )

        output_serializer = InvoiceSerializer(invoice)

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )

    # ---------------------------------------------------------
    # CREATE INVOICE FROM ORDER
    # ---------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def create_invoice_from_order(
        order,
        due_date=None,
        notes='',
        user=None
    ):

        subtotal = Decimal('0.00')

        for item in order.items.all():

            subtotal += (
                item.price * item.quantity
            )

        discount = getattr(
            order,
            'discount_amount',
            Decimal('0.00')
        ) or Decimal('0.00')

        tax_rate = Decimal('0.05')

        taxable_amount = subtotal - discount

        tax = taxable_amount * tax_rate

        total = taxable_amount + tax

        today = timezone.now()

        invoice_count = Invoice.objects.filter(
            issued_date__year=today.year,
            issued_date__month=today.month
        ).count() + 1

        invoice_number = (
            f"INV-{today.strftime('%Y-%m')}-{invoice_count:05d}"
        )

        invoice = Invoice.objects.create(

            invoice_number=invoice_number,

            order=order,

            user=order.user,

            subtotal=subtotal,

            discount_amount=discount,

            tax_amount=tax,

            total_amount=total,

            due_date=due_date,

            notes=(
                f"Customer: "
                f"{order.customer_name} "
                f"({order.customer_email}) | "
                f"{notes}"
            ),

            status='issued',

            created_by=(
                f'user_{user.id}'
                if user
                else 'user_system'
            )
        )

        for order_item in order.items.all():

            InvoiceItem.objects.create(

                invoice=invoice,

                item_name=(
                    order_item.item_name
                    or getattr(
                        order_item,
                        'name',
                        'Item'
                    )
                ),

                quantity=order_item.quantity,

                unit_price=order_item.price,

                total_price=(
                    order_item.price *
                    order_item.quantity
                )
            )

        return invoice

    # ---------------------------------------------------------
    # MARK PAID
    # ---------------------------------------------------------

    @action(
        detail=True,
        methods=['post'],
        url_path='mark-paid'
    )
    def mark_paid(self, request, id=None):

        invoice = self.get_object()

        if invoice.status in ['cancelled', 'refunded']:
           return Response(
               {'error': f'Cannot pay invoice with status: {invoice.status}'},
               status=status.HTTP_400_BAD_REQUEST
           )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        amount = serializer.validated_data.get(
            'amount',
            invoice.remaining_amount
        )

        transaction_id = (
            serializer.validated_data.get(
                'transaction_id'
            )
        )

        payment_method = (
            serializer.validated_data.get(
                'payment_method'
            )
        )

        notes = serializer.validated_data.get(
            'notes',
            ''
        )

        if amount <= 0:

            return Response(
                {
                    'error': 'Payment amount must be greater than 0.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if amount > invoice.remaining_amount:

            return Response(
                {
                    'error':
                    f'Amount exceeds remaining balance '
                    f'(Rs.{invoice.remaining_amount})'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        invoice.mark_as_paid(
            amount=amount,
            transaction_id=transaction_id
        )

        if payment_method:

            invoice.payment_method = payment_method

        if notes:

            invoice.payment_notes = notes

        invoice.save()

        output_serializer = InvoiceSerializer(
            invoice
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_200_OK
        )

    # ---------------------------------------------------------
    # CANCEL INVOICE
    # ---------------------------------------------------------

    @action(
        detail=True,
        methods=['post']
    )
    def cancel(self, request, id=None):

        invoice = self.get_object()

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        if invoice.status in [
            'paid',
            'refunded',
            'cancelled'
        ]:

            return Response(
                {
                    'error':
                    f'Cannot cancel invoice with status: '
                    f'{invoice.status}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = serializer.validated_data.get(
            'reason',
            'Cancelled by user'
        )

        invoice.mark_as_cancelled(
            reason=reason
        )

        output_serializer = InvoiceSerializer(
            invoice
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_200_OK
        )

    # ---------------------------------------------------------
    # STATISTICS
    # ---------------------------------------------------------

    @action(
        detail=False,
        methods=['get']
    )
    def stats(self, request):

        queryset = self.get_queryset()

        total_revenue = sum(
            inv.total_amount
            for inv in queryset
        )

        total_paid = sum(
            inv.amount_paid
            for inv in queryset
        )

        stats_data = {

            'total_invoices':
                queryset.count(),

            'total_revenue':
                float(total_revenue),

            'total_paid':
                float(total_paid),

            'total_pending':
                float(
                    total_revenue -
                    total_paid
                ),

            'by_status': {},

            'overdue_count':
                sum(
                    1
                    for inv in queryset
                    if inv.is_overdue
                ),

            'by_payment_method': {}
        }

        for (
            status_choice,
            status_label
        ) in Invoice.INVOICE_STATUS_CHOICES:

            invoices = queryset.filter(
                status=status_choice
            )

            count = invoices.count()

            amount = sum(
                inv.total_amount
                for inv in invoices
            )

            stats_data['by_status'][
                status_choice
            ] = {

                'count': count,

                'total_amount':
                    float(amount)
            }

        for (
            method_choice,
            method_label
        ) in Invoice.PAYMENT_METHOD_CHOICES:

            invoices = queryset.filter(
                payment_method=method_choice
            )

            count = invoices.count()

            if count > 0:

                amount = sum(
                    inv.total_amount
                    for inv in invoices
                )

                stats_data[
                    'by_payment_method'
                ][method_choice] = {

                    'count': count,

                    'total_amount':
                        float(amount)
                }

        return Response(
            stats_data,
            status=status.HTTP_200_OK
        )

    # ---------------------------------------------------------
    # DOWNLOAD PDF
    # ---------------------------------------------------------

    @action(
        detail=True,
        methods=['get'],
        url_path='download'
    )
    def download(self, request, id=None):

        # Get invoice
        invoice = self.get_object()

        # Create PDF in memory
        buffer = BytesIO()

        document = SimpleDocTemplate(

            buffer,

            pagesize=A4,

            rightMargin=15 * mm,

            leftMargin=15 * mm,

            topMargin=15 * mm,

            bottomMargin=15 * mm
        )

        styles = getSampleStyleSheet()

        # -----------------------------------------------------
        # CUSTOM STYLES
        # -----------------------------------------------------

        title_style = ParagraphStyle(

            'InvoiceTitle',

            parent=styles['Title'],

            fontSize=22,

            alignment=TA_CENTER,

            spaceAfter=15
        )

        normal_style = ParagraphStyle(

            'InvoiceNormal',

            parent=styles['Normal'],

            fontSize=10,

            spaceAfter=5
        )

        right_style = ParagraphStyle(

            'InvoiceRight',

            parent=styles['Normal'],

            fontSize=10,

            alignment=TA_RIGHT
        )

        # -----------------------------------------------------
        # PDF CONTENT
        # -----------------------------------------------------

        elements = []

        # Title
        elements.append(
            Paragraph(
                "CLOUD KITCHEN",
                title_style
            )
        )

        elements.append(
            Paragraph(
                "INVOICE",
                title_style
            )
        )

        elements.append(
            Spacer(1, 10)
        )

        # -----------------------------------------------------
        # INVOICE INFORMATION
        # -----------------------------------------------------

        invoice_info = [

            [
                Paragraph(
                    f"<b>Invoice Number:</b> "
                    f"{invoice.invoice_number}",
                    normal_style
                ),

                Paragraph(
                    f"<b>Status:</b> "
                    f"{invoice.status}",
                    right_style
                )
            ],

            [
                Paragraph(
                    f"<b>Invoice Date:</b> "
                    f"{invoice.issued_date.strftime('%d-%m-%Y')}",
                    normal_style
                ),

                Paragraph(
                    f"<b>Due Date:</b> "
                    f"{invoice.due_date.strftime('%d-%m-%Y') if invoice.due_date else 'N/A'}",
                    right_style
                )
            ]
        ]

        info_table = Table(
            invoice_info,
            colWidths=[90 * mm, 90 * mm]
        )

        info_table.setStyle(
            TableStyle([
                (
                    'VALIGN',
                    (0, 0),
                    (-1, -1),
                    'TOP'
                ),

                (
                    'BOTTOMPADDING',
                    (0, 0),
                    (-1, -1),
                    8
                )
            ])
        )

        elements.append(info_table)

        elements.append(
            Spacer(1, 10)
        )

        # -----------------------------------------------------
        # CUSTOMER DETAILS
        # -----------------------------------------------------

        customer_name = (
            getattr(
                invoice.user,
                'get_full_name',
                lambda: ''
            )()
            if invoice.user
            else 'Customer'
        )

        if not customer_name:

            customer_name = (
                getattr(
                    invoice.user,
                    'username',
                    'Customer'
                )
                if invoice.user
                else 'Customer'
            )

        customer_email = (

            getattr(
                invoice.user,
                'email',
                ''
            )

            if invoice.user

            else ''
        )

        customer_data = [

            [
                Paragraph(
                    "<b>Bill To:</b>",
                    normal_style
                )
            ],

            [
                Paragraph(
                    customer_name,
                    normal_style
                )
            ],

            [
                Paragraph(
                    customer_email,
                    normal_style
                )
            ]
        ]

        customer_table = Table(
            customer_data,
            colWidths=[180 * mm]
        )

        customer_table.setStyle(
            TableStyle([
                (
                    'BOX',
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    'BACKGROUND',
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    'LEFTPADDING',
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    'TOPPADDING',
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    'BOTTOMPADDING',
                    (0, 0),
                    (-1, -1),
                    5
                )
            ])
        )

        elements.append(
            customer_table
        )

        elements.append(
            Spacer(1, 15)
        )

        # -----------------------------------------------------
        # ITEMS TABLE
        # -----------------------------------------------------

        item_data = [

            [
                Paragraph(
                    "<b>Item</b>",
                    normal_style
                ),

                Paragraph(
                    "<b>Qty</b>",
                    normal_style
                ),

                Paragraph(
                    "<b>Unit Price</b>",
                    normal_style
                ),

                Paragraph(
                    "<b>Total</b>",
                    normal_style
                )
            ]
        ]

        items = InvoiceItem.objects.filter(
            invoice=invoice
        )

        for item in items:

            item_data.append(

                [

                    str(item.item_name),

                    str(item.quantity),

                    f"₹{item.unit_price:.2f}",

                    f"₹{item.total_price:.2f}"
                ]
            )

        if len(item_data) == 1:

            item_data.append(
                [
                    "No items",
                    "",
                    "",
                    ""
                ]
            )

        items_table = Table(

            item_data,

            colWidths=[
                75 * mm,
                25 * mm,
                40 * mm,
                40 * mm
            ]
        )

        items_table.setStyle(

            TableStyle([

                (
                    'BACKGROUND',
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    'GRID',
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    'ALIGN',
                    (1, 1),
                    (-1, -1),
                    'RIGHT'
                ),

                (
                    'VALIGN',
                    (0, 0),
                    (-1, -1),
                    'MIDDLE'
                ),

                (
                    'LEFTPADDING',
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    'RIGHTPADDING',
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    'TOPPADDING',
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    'BOTTOMPADDING',
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        elements.append(
            items_table
        )

        elements.append(
            Spacer(1, 15)
        )

        # -----------------------------------------------------
        # AMOUNT SUMMARY
        # -----------------------------------------------------

        summary_data = [

            [
                "Subtotal",
                f"₹{invoice.subtotal:.2f}"
            ],

            [
                "Discount",
                f"₹{invoice.discount_amount:.2f}"
            ],

            [
                "Tax",
                f"₹{invoice.tax_amount:.2f}"
            ],

            [
                "Total Amount",
                f"₹{invoice.total_amount:.2f}"
            ],

            [
                "Amount Paid",
                f"₹{invoice.amount_paid:.2f}"
            ],

            [
                "Remaining Amount",
                f"₹{invoice.remaining_amount:.2f}"
            ]
        ]

        summary_table = Table(

            summary_data,

            colWidths=[
                120 * mm,
                60 * mm
            ]
        )

        summary_table.setStyle(

            TableStyle([

                (
                    'ALIGN',
                    (1, 0),
                    (1, -1),
                    'RIGHT'
                ),

                (
                    'GRID',
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    'FONTNAME',
                    (0, 3),
                    (-1, 3),
                    'Helvetica-Bold'
                ),

                (
                    'FONTNAME',
                    (0, 5),
                    (-1, 5),
                    'Helvetica-Bold'
                ),

                (
                    'BACKGROUND',
                    (0, 3),
                    (-1, 3),
                    colors.lightgrey
                ),

                (
                    'LEFTPADDING',
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    'RIGHTPADDING',
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    'TOPPADDING',
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    'BOTTOMPADDING',
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        elements.append(
            summary_table
        )

        elements.append(
            Spacer(1, 20)
        )

        # -----------------------------------------------------
        # PAYMENT INFORMATION
        # -----------------------------------------------------

        payment_method = (
            invoice.payment_method
            if invoice.payment_method
            else "Not specified"
        )

        elements.append(

            Paragraph(

                f"<b>Payment Method:</b> "
                f"{payment_method}",

                normal_style
            )
        )

        if invoice.transaction_id:

            elements.append(

                Paragraph(

                    f"<b>Transaction ID:</b> "
                    f"{invoice.transaction_id}",

                    normal_style
                )
            )

        # -----------------------------------------------------
        # NOTES
        # -----------------------------------------------------

        if invoice.notes:

            elements.append(
                Spacer(1, 10)
            )

            elements.append(

                Paragraph(

                    f"<b>Notes:</b> "
                    f"{invoice.notes}",

                    normal_style
                )
            )

        elements.append(
            Spacer(1, 20)
        )

        elements.append(

            Paragraph(

                "Thank you for choosing Cloud Kitchen!",

                ParagraphStyle(

                    'Footer',

                    parent=normal_style,

                    alignment=TA_CENTER,

                    fontSize=9
                )
            )
        )

        # -----------------------------------------------------
        # BUILD PDF
        # -----------------------------------------------------

        document.build(elements)

        pdf = buffer.getvalue()

        buffer.close()

        # -----------------------------------------------------
        # RETURN PDF RESPONSE
        # -----------------------------------------------------

        response = HttpResponse(
            pdf,
            content_type='application/pdf'
        )

        response[
            'Content-Disposition'
        ] = (
            f'attachment; '
            f'filename="{invoice.invoice_number}.pdf"'
        )

        return response