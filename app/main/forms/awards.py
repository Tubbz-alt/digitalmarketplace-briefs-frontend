from flask_wtf import FlaskForm
from wtforms import RadioField, validators
from dmutils.forms.helpers import govuk_options


class AwardedBriefResponseForm(FlaskForm):
    """Form for the buyer to tell us which BriefResponse was awarded a contract
    """
    # BriefResponse choices expected to be set at runtime
    brief_response = RadioField(
        "Winning BriefResponse",
        validators=[validators.DataRequired(message="Select a supplier.")],
        coerce=int
    )

    def __init__(self, brief_responses, *args, **kwargs):
        """
            Requires extra argument:
             - `brief_responses` - list of BriefResponses for the multiple choice
        """
        super(AwardedBriefResponseForm, self).__init__(*args, **kwargs)

        brief_responses = list(
            sorted(
                [{'id': b['id'], 'name': b['supplierName']} for b in brief_responses],
                key=lambda x: x['name']
            )
        )

        self.brief_response.choices = [(br['id'], br['name']) for br in brief_responses]
        self.brief_response.govuk_options = govuk_options(
            [{"value": br['id'], "label": br['name']} for br in brief_responses]
        )
