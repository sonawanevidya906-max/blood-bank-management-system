from django.shortcuts import render, redirect
from django.db.models import Sum
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages

from . import models, forms
from donor import models as dmodels
from patient import models as pmodels
from donor import forms as dforms
from patient import forms as pforms
from .forms import ContactForm


# ---------- Home / Index Page ----------
def home_view(request):
    if models.Stock.objects.count() == 0:
        blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        for bg in blood_groups:
            models.Stock.objects.create(bloodgroup=bg)

    stock = models.Stock.objects.all()
    contact_form = ContactForm()
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            contact = contact_form.save()
            send_mail(
                subject=f"New Contact Message from {contact.name}",
                message=f"Message: {contact.message}\n\nPhone: {contact.phone}\nEmail: {contact.email}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=settings.EMAIL_RECEIVING_USER,
                fail_silently=False,
            )
            messages.success(request, "Thank you! Your message has been sent.")
            return redirect('home')

    context = {'stock': stock, 'form': contact_form}
    if request.user.is_authenticated:
        return redirect('afterlogin')
    return render(request, 'blood/index.html', context)





# ---------- User Type Checks ----------
def is_donor(user):
    return user.groups.filter(name='DONOR').exists()


def is_patient(user):
    return user.groups.filter(name='PATIENT').exists()


# ---------- After Login Redirect ----------
def afterlogin_view(request):
    if is_donor(request.user):
        return redirect('donor-dashboard')
    elif is_patient(request.user):
        return redirect('patient-dashboard')
    else:
        return redirect('admin-dashboard')


# ---------- Admin Dashboard ----------
@login_required(login_url='adminlogin')
def admin_dashboard_view(request):

    totalunit = models.Stock.objects.aggregate(Sum('unit'))

    context = {
        'A1': models.Stock.objects.get(bloodgroup="A+"),
        'A2': models.Stock.objects.get(bloodgroup="A-"),
        'B1': models.Stock.objects.get(bloodgroup="B+"),
        'B2': models.Stock.objects.get(bloodgroup="B-"),
        'AB1': models.Stock.objects.get(bloodgroup="AB+"),
        'AB2': models.Stock.objects.get(bloodgroup="AB-"),
        'O1': models.Stock.objects.get(bloodgroup="O+"),
        'O2': models.Stock.objects.get(bloodgroup="O-"),

        'totaldonors': dmodels.Donor.objects.count(),
        'totalbloodunit': totalunit['unit__sum'],
        'totalrequest': models.BloodRequest.objects.count(),
        'totalapprovedrequest': models.BloodRequest.objects.filter(status='Approved').count(),
         

    }

    return render(request, 'blood/admin_dashboard.html', context)


# ---------- Contact Page ----------
def contact_view(request):
    form = ContactForm()
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()  # Database मध्ये save होईल
            
            # Admin ला email notification
            try:
                send_mail(
                    subject=f"New Contact Message from {contact.name}",
                    message=f"Message: {contact.message}\n\nPhone: {contact.phone}\nEmail: {contact.email}",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=settings.EMAIL_RECEIVING_USER,
                    fail_silently=False,
                )
            except Exception as e:
                print("Email sending error:", e)
            
            messages.success(request, "Thank you! Your message has been sent successfully.")
            return redirect('contact')
    return render(request, 'blood/index.html', {'form': form})



# ---------- Admin Contact View ----------

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from . import models

@login_required(login_url='adminlogin')
def admin_contact_view(request):
    q = request.GET.get('q', '')  # Search term
    
    if q:
        contacts_list = models.Contact.objects.filter(name__icontains=q).order_by('-date_submitted')
    else:
        contacts_list = models.Contact.objects.all().order_by('-date_submitted')

    paginator = Paginator(contacts_list, 10)  # 10 messages per page
    page_number = request.GET.get('page')
    contacts = paginator.get_page(page_number)

    new_messages = models.Contact.objects.filter(is_read=False).count()

    return render(request, 'blood/admin_contact.html', {
        'contacts': contacts,
        'new_messages': new_messages,
        'q': q,  # template मध्ये search term ठेवण्यासाठी
    })




@login_required(login_url='adminlogin')
def delete_contact_view(request, pk):
    contact = models.Contact.objects.get(id=pk)
    contact.delete()
    return redirect('admin-contacts')
   

import csv
from django.http import HttpResponse

def export_contacts(request):

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contacts.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name','Email','Phone','Message'])

    contacts = models.Contact.objects.all()

    for c in contacts:
        writer.writerow([c.name,c.email,c.phone,c.message])

    return response



# ---------- Admin Blood Stock ----------
@login_required(login_url='adminlogin')
def admin_blood_view(request):
    context = {
        'bloodForm': forms.BloodForm(),
        'A1': models.Stock.objects.get(bloodgroup="A+"),
        'A2': models.Stock.objects.get(bloodgroup="A-"),
        'B1': models.Stock.objects.get(bloodgroup="B+"),
        'B2': models.Stock.objects.get(bloodgroup="B-"),
        'AB1': models.Stock.objects.get(bloodgroup="AB+"),
        'AB2': models.Stock.objects.get(bloodgroup="AB-"),
        'O1': models.Stock.objects.get(bloodgroup="O+"),
        'O2': models.Stock.objects.get(bloodgroup="O-"),
    }
    if request.method == 'POST':
        bloodForm = forms.BloodForm(request.POST)
        if bloodForm.is_valid():
            bloodgroup = bloodForm.cleaned_data['bloodgroup']
            stock = models.Stock.objects.get(bloodgroup=bloodgroup)
            stock.unit = bloodForm.cleaned_data['unit']
            stock.save()
        return redirect('admin-blood')
    return render(request, 'blood/admin_blood.html', context)


# ---------- Admin Donor ----------
@login_required(login_url='adminlogin')
def admin_donor_view(request):
    donors = dmodels.Donor.objects.all()
    return render(request, 'blood/admin_donor.html', {'donors': donors})


@login_required(login_url='adminlogin')
def update_donor_view(request, pk):
    donor = dmodels.Donor.objects.get(id=pk)
    user = User.objects.get(id=donor.user_id)
    userForm = dforms.DonorUserForm(instance=user)
    donorForm = dforms.DonorForm(request.FILES, instance=donor)
    context = {'userForm': userForm, 'donorForm': donorForm}

    if request.method == 'POST':
        userForm = dforms.DonorUserForm(request.POST, instance=user)
        donorForm = dforms.DonorForm(request.POST, request.FILES, instance=donor)
        if userForm.is_valid() and donorForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            donor = donorForm.save(commit=False)
            donor.user = user
            donor.bloodgroup = donorForm.cleaned_data['bloodgroup']
            donor.save()
            return redirect('admin-donor')
    return render(request, 'blood/update_donor.html', context)


@login_required(login_url='adminlogin')
def delete_donor_view(request, pk):
    donor = dmodels.Donor.objects.get(id=pk)
    user = User.objects.get(id=donor.user_id)
    user.delete()
    donor.delete()
    return redirect('admin-donor')


# ---------- Admin Patient ----------
@login_required(login_url='adminlogin')
def admin_patient_view(request):
    patients = pmodels.Patient.objects.all()
    return render(request, 'blood/admin_patient.html', {'patients': patients})


@login_required(login_url='adminlogin')
def update_patient_view(request, pk):
    patient = pmodels.Patient.objects.get(id=pk)
    user = User.objects.get(id=patient.user_id)
    userForm = pforms.PatientUserForm(instance=user)
    patientForm = pforms.PatientForm(request.FILES, instance=patient)
    context = {'userForm': userForm, 'patientForm': patientForm}

    if request.method == 'POST':
        userForm = pforms.PatientUserForm(request.POST, instance=user)
        patientForm = pforms.PatientForm(request.POST, request.FILES, instance=patient)
        if userForm.is_valid() and patientForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            patient = patientForm.save(commit=False)
            patient.user = user
            patient.bloodgroup = patientForm.cleaned_data['bloodgroup']
            patient.save()
            return redirect('admin-patient')
    return render(request, 'blood/update_patient.html', context)


@login_required(login_url='adminlogin')
def delete_patient_view(request, pk):
    patient = pmodels.Patient.objects.get(id=pk)
    user = User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-patient')


# ---------- Admin Blood Requests ----------
@login_required(login_url='adminlogin')
def admin_request_view(request):
    requests = models.BloodRequest.objects.filter(status='Pending')
    return render(request, 'blood/admin_request.html', {'requests': requests})


@login_required(login_url='adminlogin')
def admin_request_history_view(request):
    requests = models.BloodRequest.objects.exclude(status='Pending')
    return render(request, 'blood/admin_request_history.html', {'requests': requests})


@login_required(login_url='adminlogin')
def update_approve_status_view(request, pk):
    req = models.BloodRequest.objects.get(id=pk)
    stock = models.Stock.objects.get(bloodgroup=req.bloodgroup)
    message = None
    if stock.unit >= req.unit:
        stock.unit -= req.unit
        stock.save()
        req.status = 'Approved'
    else:
        message = f"Stock does not have enough units. Only {stock.unit} units available."
    req.save()
    requests = models.BloodRequest.objects.filter(status='Pending')
    return render(request, 'blood/admin_request.html', {'requests': requests, 'message': message})


@login_required(login_url='adminlogin')
def update_reject_status_view(request, pk):
    req = models.BloodRequest.objects.get(id=pk)
    req.status = 'Rejected'
    req.save()
    return redirect('admin-request')


# ---------- Admin Donations ----------
@login_required(login_url='adminlogin')
def admin_donation_view(request):
    donations = dmodels.BloodDonate.objects.all()
    return render(request, 'blood/admin_donation.html', {'donations': donations})


@login_required(login_url='adminlogin')
def approve_donation_view(request, pk):
    donation = dmodels.BloodDonate.objects.get(id=pk)
    stock = models.Stock.objects.get(bloodgroup=donation.bloodgroup)
    stock.unit += donation.unit
    stock.save()
    donation.status = 'Approved'
    donation.save()
    return redirect('admin-donation')


@login_required(login_url='adminlogin')
def reject_donation_view(request, pk):
    donation = dmodels.BloodDonate.objects.get(id=pk)
    donation.status = 'Rejected'
    donation.save()
    return redirect('admin-donation')

