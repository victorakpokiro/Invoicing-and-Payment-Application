from wtforms import Form, validators, Field
from wtforms.fields import (BooleanField, StringField, 
                            TextField, SubmitField, DateField, 
                            IntegerField, TextAreaField, SelectField)
from wtforms.validators import InputRequired, Email, Length, ValidationError

from wtforms import form, validators, fields
from wtforms.form import Form
# from wtforms.fields import 
# from wtforms.validators import ValidationError, InputRequired, Length, Email



def input_required():

    def check_required(form, field):
        if not field.data:
            raise ValidationError("field is required.")

    return check_required


# def length(min=3, max=40):

#     def _length(form, field):

#         if len(field.data) < min:
#             raise ValidationError("minimum length of %d"%min)

#         if len(field.data) > max:
#             raise ValidationError("max field length exceed")


#     return _length


# def input_required():

#     def check_length( form, field ):
#         if not field.data:
#             raise ValidationError("input is required")

#     return check_length


def length( min=3, max=12 ):

    def _length(form, field):

        _field = str(field.data)
        if len(_field) < min:
            raise ValidationError("Length of field must be greater than %d"%min)

        if len(_field) > max:
            raise ValidationError("Length of Field Exceeded")

    return _length



def check_inp_length():

    def validate_amount(form, field):
        try: 
            float(field.data)
        except Exception as e:
            raise ValidationError('valid input required.')

    return validate_amount


def check_sign():

    def negative(form, field):
        if float(field.data) < 1:
            raise ValidationError("valid input required.")

    return negative

class CustomerForm(Form):
    name = StringField('name', [input_required()])
    address = StringField('address', [input_required()])
    email = StringField('email', [input_required(), Email()])
    phone = StringField('phone', [input_required()])
    postal_code = IntegerField('postal_code')


# class ItemsForm(Form):
#     desc = StringField('desc', [input_required()])
#     qty = IntegerField('qty', [input_required()])
#     rate = IntegerField('rate', [input_required()])
#     amount = StringField('amount', [input_required(), length()])

#     def validate_amount(form, field):
        
#         try:
#             float(field.data)
#         except Exception as e:
#             raise ValidationError('Invalid amount value specified.')


class ItemForm(Form):
    item_desc = TextAreaField('Description :', [InputRequired()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    qty = IntegerField('Quantity :', [InputRequired(), check_sign()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    rate = IntegerField('Rate :', [InputRequired(), check_sign()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    amt = IntegerField('Amount :', 
                                render_kw={"class_": "form-control", 
                                            "readonly": "readonly"})


class DiscountFrm(Form):
    discount_type = SelectField('Discount Type :', 
                                choices=[('select', 'Select...'), 
                                         ('fixed', 'Fixed'), 
                                         ('percent', 'Percentage')], 
                                render_kw={"class_": "form-control", 
                                           "style": "margin-bottom : 10px"})

    discount = IntegerField('Discount Applied :', [length(min=1)], 
                            render_kw={"class_": "form-control", 
                                       "autocomplete": "off"})

    disc_amt = IntegerField('Discount Value :', 
                            render_kw={"class_": "form-control", 
                                       "readonly": "readonly"})

    sub_total = IntegerField('Sub-Total :', [check_inp_length()], 
                             render_kw={"class_": "form-control", 
                                        "readonly": "readonly"})

    new_total = IntegerField('New Total :', 
                             render_kw={"class_": "form-control", 
                                     "readonly": "readonly"
                                    })


class CreateInvoiceForm(Form):
    name = StringField('Name :', [InputRequired()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    address = TextAreaField('Address :', [InputRequired()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    email = StringField('Email :', [InputRequired(), Email()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    phone = StringField('Phone Number :', [InputRequired(), length(), 
                                                check_inp_length()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    post_addr = StringField('Postal-Address :', [InputRequired()], 
                                render_kw={"class_": "form-control"})
    currency = SelectField('Currency :', 
                                choices=[
                                        ('select', 'Select...'),
                                        ('ngn', 'NGN'), 
                                        ('ghc', 'GHC'), 
                                        ('usd', 'USD'),
                                        ('eur', 'EUR')], 
                                render_kw={"class_": "form-control", 
                                           "style": "margin-bottom : 10px"})



class BillsForm(Form):
    disc_type = StringField('disc_type', [input_required()])
    disc_value = IntegerField('disc_value')
    amtPaid = IntegerField('amtPaid', [input_required()])
    currency = StringField('cur', [input_required()])

    def validate_disc_type(form, field):

        if field.data not in ['fixed', 'percentage']:
            raise ValidationError('Invalid discount type specified')
