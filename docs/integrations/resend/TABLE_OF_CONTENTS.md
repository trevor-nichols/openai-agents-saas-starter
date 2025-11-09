.
├── API_Keys/                    # API documentation for managing API keys
│   ├── DEL_delete-api-key.md    # API documentation for deleting an API key
│   ├── GET_list-api-keys.md     # API documentation for listing API keys
│   └── POST_create-api-key.md   # API documentation for creating an API key
├── Broadcasts/                  # API documentation for managing email broadcasts
│   ├── DEL_delete-broadcast.md  # API documentation for deleting a broadcast
│   ├── GET_list-broadcasts.md   # API documentation for listing broadcasts
│   ├── GET_retrieve-broadcast.md # API documentation for retrieving a single broadcast
│   ├── PATCH_update-broadcast.md # API documentation for updating a broadcast
│   ├── POST_create-broadcast.md # API documentation for creating a new broadcast
│   └── POST_send-broadcast.md   # API documentation for sending a broadcast
├── Contact_Properties/          # API documentation for managing custom properties for contacts
│   ├── DEL_delete-contact-property.md # API documentation for deleting a contact property
│   ├── GET_list-contact-properties.md # API documentation for listing contact properties
│   ├── GET_retrieve-contact-property.md # API documentation for retrieving a single contact property
│   ├── PATCH_update-contact-property.md # API documentation for updating a contact property
│   └── POST_create-contact-property.md # API documentation for creating a new contact property
├── Contacts/                    # API documentation for managing contacts
│   ├── DEL_delete-contact-segment.md # API documentation for removing a contact from a segment
│   ├── DEL_delete-contact.md    # API documentation for deleting a contact
│   ├── GET_list-contact-segments.md # API documentation for listing segments a contact belongs to
│   ├── GET_list-contacts.md     # API documentation for listing all contacts
│   ├── GET_retrieve-contact-topics.md # API documentation for retrieving topic subscriptions for a contact
│   ├── GET_retrieve-contact.md  # API documentation for retrieving a single contact
│   ├── PATCH_update-contact-topics.md # API documentation for updating a contact's topic subscriptions
│   ├── PATCH_update-contact.md  # API documentation for updating a contact
│   ├── POST_add-contact-to-segment.md # API documentation for adding a contact to a segment
│   └── POST_create-contact.md   # API documentation for creating a new contact
├── Domains/                     # API documentation for managing sending domains
│   ├── DEL_delete-domain.md     # API documentation for deleting a domain
│   ├── GET_list-domains.md      # API documentation for listing all domains
│   ├── GET_retrieve-domain.md   # API documentation for retrieving a single domain
│   ├── PATCH_update-domain.md   # API documentation for updating a domain's settings
│   ├── POST_create-domain.md    # API documentation for creating a new domain
│   └── POST_verify-domain.md    # API documentation for verifying a domain
├── Receiving/                   # API documentation for handling received emails
│   ├── GET_list-attachments.md  # API documentation for listing attachments of a received email
│   ├── GET_list-received-emails.md # API documentation for listing all received emails
│   ├── GET_retrieve-attachment.md # API documentation for retrieving a single attachment from a received email
│   └── GET_retrieve-received-email.md # API documentation for retrieving a single received email
├── Segments/                    # API documentation for managing contact segments
│   ├── DEL_delete-segment.md    # API documentation for deleting a segment
│   ├── GET_list-segments.md     # API documentation for listing all segments
│   ├── GET_retrieve-segment.md  # API documentation for retrieving a single segment
│   └── POST_create-segment.md   # API documentation for creating a new segment
├── Sending/                     # API documentation for sending emails
│   ├── GET_list-attachments.md  # API documentation for listing attachments of a sent email
│   ├── GET_list-emails.md       # API documentation for listing sent emails
│   ├── GET_retrieve-attachment.md # API documentation for canceling a scheduled email
│   ├── GET_retrieve-email.md    # API documentation for retrieving a single sent email
│   ├── PATCH_update-email.md    # API documentation for updating a scheduled email
│   ├── POST_cancel-email.md     # API documentation for canceling a scheduled email
│   ├── POST_send-batch-emails.md # API documentation for sending emails in a batch
│   └── POST_send-email.md       # API documentation for sending a single email
├── Templates/                   # API documentation for managing email templates
│   ├── DEL_delete-template.md   # API documentation for deleting an email template
│   ├── GET_get-template.md      # API documentation for retrieving a single email template
│   ├── GET_list-templates.md    # API documentation for listing all email templates
│   ├── PATCH_update-template.md # API documentation for updating an email template
│   ├── POST_create-template.md  # API documentation for creating a new email template
│   ├── POST_duplicate-template.md # API documentation for duplicating an email template
│   └── POST_publish-template.md # API documentation for publishing an email template
├── Topics/                      # API documentation for managing subscription topics
│   ├── DEL_delete-topic.md      # API documentation for deleting a topic
│   ├── GET_list-topics.md       # API documentation for listing all topics
│   ├── GET_retrieve-topic.md    # API documentation for retrieving a single topic
│   ├── PATCH_update-topic.md    # API documentation for updating a topic
│   └── POST_create-topic.md     # API documentation for creating a new topic
├── Webhooks/                    # API documentation for managing webhooks
│   ├── DEL_delete-webhook.md    # API documentation for deleting a webhook
│   ├── GET_list-webhooks.md     # API documentation for listing all webhooks
│   ├── GET_retrieve-webhook.md  # API documentation for retrieving a single webhook
│   ├── PATCH_update-webhook.md  # API documentation for updating a webhook
│   └── POST_create-webhook.md   # API documentation for creating a new webhook
└── sdk/                         # Contains SDK-related documentation
    └── sdk_overview.md          # Overview and usage examples for the Resend Python SDK