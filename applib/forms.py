from wtforms import Form, validators, Field
from wtforms.fields import BooleanField, StringField, IntegerField, TextField
from wtforms.validators import InputRequired, Email, length, ValidationError



def input_required():

    def check_required(form, field):
        if not field.data:
            raise ValidationError("field is required.")

    return check_required


def length(min=3, max=40):

    def _length(form, field):

        if len(field.data) < min:
            raise ValidationError("minimum length of %d"%min)

        if len(field.data) > max:
            raise ValidationError("max field length exceed")


    return _length


class CustomerForm(Form):
    name = StringField('name', [input_required()])
    address = StringField('address', [input_required()])
    email = StringField('email', [input_required(), Email()])
    phone = StringField('phone', [input_required()])
    postal_code = IntegerField('postal_code')


class ItemsForm(Form):
    desc = StringField('desc', [input_required()])
    qty = IntegerField('qty', [input_required()])
    rate = IntegerField('rate', [input_required()])
    amount = StringField('amount', [input_required(), length()])

    def validate_amount(form, field):
        
        try:
            float(field.data)
        except Exception as e:
            raise ValidationError('Invalid amount value specified.')


class BillsForm(Form):
    disc_type = StringField('disc_type', [input_required()])
    disc_value = IntegerField('disc_value')
    amtPaid = IntegerField('amtPaid', [input_required()])
    currency = StringField('cur', [input_required()])

    def validate_disc_type(form, field):

        if field.data not in ['fixed', 'percentage']:
            raise ValidationError('Invalid discount type specified')
