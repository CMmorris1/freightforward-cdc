from flask_wtf import FlaskForm
from wtforms.fields import StringField, PasswordField, SubmitField, SelectField, SelectMultipleField, BooleanField
from wtforms.widgets import TextArea
from wtforms.validators import ValidationError, DataRequired, InputRequired, Email, EqualTo, Length, Optional
from flask_server.models.freight_db_models import db, API_User

#=========================== Custom Validators ============================================================================

#------------------------------------------------------------------------------------------------------------------------------------------------
# Not Registered
#=========================================
#   * Verifies an API User is not already registered. Checks that no entry in the api_user table exists with the corresponding email
#
# Raises: 
#   * ValidationError - message = "Email address already registered"
#------------------------------------------------------------------------------------------------------------------------------------------------
def not_registered(form, field):
    user = API_User.query.filter_by(email=field.data).first()
    if user:
        raise ValidationError('Email address already registered.')

#------------------------------------------------------------------------------------------------------------------------------------------------
# User Exists
#=========================================
#   * Verifies an API User with the corresponding email does exist in the api_user table
#
# Raises: 
#   * ValidationError - message = "No account with this email address was found."
#------------------------------------------------------------------------------------------------------------------------------------------------
def user_exists(form, field):
    user = API_User.query.filter_by(email=field.data).first()
    if not user:
        raise ValidationError('No account with this email address was found.')
      
#------------------------------------------------------------------------------------------------------------------------------------------------
# Not Locked
#=========================================
#   * Verifies the API User account with the corresponding email is not locked
#
# Raises: 
#   * ValidationError - message = "This account has been locked out from too many failed login attemps. Please contact an administrator."
#------------------------------------------------------------------------------------------------------------------------------------------------
def not_locked(form, field):
    user = API_User.query.filter_by(email=form.email.data).first()
    if user:
        if user.locked:
            raise ValidationError('This account has been locked out from too many failed login attemps. Please contact an administrator.')

#------------------------------------------------------------------------------------------------------------------------------------------------
# Required if False
#=========================================
#   * Verifies a justification has been provided if a permissions request has been rejected
#
# Raises: 
#   * ValidationError - message = "Justification is required for rejected requests."
#------------------------------------------------------------------------------------------------------------------------------------------------
def required_if_false(form, field):
    approved = bool(form.approve.data)
    justification = form.justification.data

    if not approved and (not justification or justification == ''):
        raise ValidationError('Justification is required for rejected requests.')


#=========================== Flask Form Objects ============================================================================ 

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=40), not_registered])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    passwordConf = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Submit')


class RegisterAppForm(FlaskForm):
    name = StringField('Name of Application', validators=[DataRequired()])
    version = StringField('Version', validators=[DataRequired()])
    sdsps = SelectMultipleField('SDSPs Requested (with HTTP Methods)', validators=[DataRequired()])
    justification = StringField('Justification', validators=[DataRequired(), Length(max=100)], widget=TextArea(), )
    submit = SubmitField('Submit')


class AddressPermissionRequestForm(FlaskForm):
    approve = SelectField('Approve Request', coerce=int, choices=[(0, 'No'), (1, 'Yes')])
    justification = StringField('Justification', validators=[required_if_false, Length(max=100)], widget=TextArea())
    submit = SubmitField('Submit')


class AddAppPermissionsForm(FlaskForm):
    name = StringField('App Name: ', validators=[Optional()])
    version = StringField('Version: ', validators=[Optional()])
    sdsps = SelectMultipleField('Available SDSP Permissions', validators=[DataRequired()])
    justification = StringField('Justification', validators=[DataRequired(), Length(max=100)], widget=TextArea(), )
    submit = SubmitField('Submit')
    

class RemoveAppPermissionsForm(FlaskForm):
    name = StringField('App Name: ', validators=[Optional()])
    version = StringField('Version: ', validators=[Optional()])
    sdsps = SelectMultipleField('Available SDSP Permissions', validators=[Optional()])
    justification = StringField('Justification', validators=[Optional(), Length(max=100)], widget=TextArea(), )
    submit = SubmitField('Submit')
    