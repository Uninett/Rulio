from django.core.exceptions import NON_FIELD_ERRORS


# Turns a Django ValidationError into readable text, like "Name: This field cannot be blank."
# Errors that belong to no single field, like a unique constraint, are shown without a field name.
# object_label is put in front of field names, so "Interface" gives "Interface name: ...".
def validation_error_message(error, object_label=None):
    messages = []
    for field, field_messages in error.message_dict.items():
        for message in field_messages:
            if field == NON_FIELD_ERRORS:
                messages.append(message)
                continue
            field_label = field.replace("_", " ")
            field_label = f"{object_label} {field_label}" if object_label else field_label[0].upper() + field_label[1:]
            messages.append(f"{field_label}: {message}")
    return " ".join(messages)
