from django import forms
from django.utils.translation import ugettext_lazy as _

from allauth.account.adapter import get_adapter

from .models import Invitation
from .exceptions import AlreadyInvited, AlreadyAccepted


class CleanEmailMixin(object):

    def validate_invitation(self, email):
        if Invitation.objects.all_valid().filter(
                email__iexact=email, accepted=False):
            raise AlreadyInvited
        elif Invitation.objects.filter(
                email__iexact=email, accepted=True):
            raise AlreadyAccepted
        else:
            return True

    def clean_email(self):
        email = self.cleaned_data["email"]
        email = get_adapter().clean_email(email)

        errors = {
            "already_invited": _("This e-mail address has already been"
                                 " invited."),
            "already_accepted": _("This e-mail address has already"
                                  " accepted an invite."),
        }
        try:
            self.validate_invitation(email)
        except(AlreadyInvited):
            raise forms.ValidationError(errors["already_invited"])
        except(AlreadyAccepted):
            raise forms.ValidationError(errors["already_accepted"])

        return email


class InviteForm(forms.Form, CleanEmailMixin):

    email = forms.EmailField(
        label=_("E-mail"),
        required=True,
        widget=forms.TextInput(attrs={"type": "email", "size": "30"}))

    def save(self, email):
        return Invitation.create(email=email)


class InvitationAdminAddForm(forms.ModelForm, CleanEmailMixin):
    email = forms.EmailField(
        label=_("E-mail"),
        required=True,
        widget=forms.TextInput(attrs={"type": "email", "size": "30"}))

    def save(self, *args, **kwargs):
        cleaned_data = super(InvitationAdminAddForm, self).clean()
        email = cleaned_data.get("email")
        instance = Invitation.create(email=email)
        instance.send_invitation(self.request)
        super(InvitationAdminAddForm, self).save(*args, **kwargs)
        return instance

    class Meta:
        model = Invitation
        fields = ("email", )


class InvitationAdminChangeForm(forms.ModelForm):

    class Meta:
        model = Invitation
        fields = '__all__'
