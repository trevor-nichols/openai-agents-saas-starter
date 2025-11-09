# Update Contact

> Update an existing contact.

export const ResendParamField = ({children, body, path, ...props}) => {
  const [lang, setLang] = useState(() => {
    return localStorage.getItem('code') || '"Node.js"';
  });
  useEffect(() => {
    const onStorage = event => {
      const key = event.detail.key;
      if (key === 'code') {
        setLang(event.detail.value);
      }
    };
    document.addEventListener('mintlify-localstorage', onStorage);
    return () => {
      document.removeEventListener('mintlify-localstorage', onStorage);
    };
  }, []);
  const toCamelCase = str => typeof str === 'string' ? str.replace(/[_-](\w)/g, (_, c) => c.toUpperCase()) : str;
  const resolvedBody = useMemo(() => {
    const value = JSON.parse(lang);
    return value === 'Node.js' ? toCamelCase(body) : body;
  }, [body, lang]);
  const resolvedPath = useMemo(() => {
    const value = JSON.parse(lang);
    return value === 'Node.js' ? toCamelCase(path) : path;
  }, [path, lang]);
  return <ParamField body={resolvedBody} path={resolvedPath} {...props}>
      {children}
    </ParamField>;
};

## Path Parameters

Either `id` or `email` must be provided.

<ParamField path="id" type="string">
  The Contact ID.
</ParamField>

<ParamField path="email" type="string">
  The Contact Email.
</ParamField>

## Body Parameters

<ResendParamField body="first_name" type="string">
  The first name of the contact.
</ResendParamField>

<ResendParamField body="last_name" type="string">
  The last name of the contact.
</ResendParamField>

<ParamField body="unsubscribed" type="boolean">
  The Contact's global subscription status. If set to `true`, the contact will
  be unsubscribed from all Broadcasts.
</ParamField>

<ParamField body="properties" type="object">
  A map of custom property keys and values to update.

  <Expandable defaultOpen="true" title="custom properties">
    <ParamField body="key" type="string" required>
      The property key.
    </ParamField>

    <ParamField body="value" type="string" required>
      The property value.
    </ParamField>
  </Expandable>
</ParamField>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  // Update by contact id
  const { data, error } = await resend.contacts.update({
    id: 'e169aa45-1ecf-4183-9955-b1499d5701d3',
    unsubscribed: true,
  });

  // Update by contact email
  const { data, error } = await resend.contacts.update({
    email: 'acme@example.com',
    unsubscribed: true,
  });
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  // Update by contact id
  $resend->contacts->update(
    id: 'e169aa45-1ecf-4183-9955-b1499d5701d3',
    parameters: [
      'unsubscribed' => true
    ]
  );

  // Update by contact email
  $resend->contacts->update(
    email: 'acme@example.com',
    parameters: [
      'unsubscribed' => true
    ]
  );
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"

  # Update by contact id
  params: resend.Contacts.UpdateParams = {
    "id": "e169aa45-1ecf-4183-9955-b1499d5701d3",
    "unsubscribed": True,
  }

  resend.Contacts.update(params)

  # Update by contact email
  params: resend.Contacts.UpdateParams = {
    "email": "acme@example.com",
    "unsubscribed": True,
  }

  resend.Contacts.update(params)
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  # Update by contact id
  params = {
    "id": "e169aa45-1ecf-4183-9955-b1499d5701d3",
    "unsubscribed": true,
  }

  Resend::Contacts.update(params)

  # Update by contact email
  params = {
    "email": "acme@example.com",
    "unsubscribed": true,
  }

  Resend::Contacts.update(params)
  ```

  ```go Go theme={null}
  import "github.com/resend/resend-go/v3"

  client := resend.NewClient("re_xxxxxxxxx")

  // Update by contact id
  params := &resend.UpdateContactRequest{
    Id:           "e169aa45-1ecf-4183-9955-b1499d5701d3",
    Unsubscribed: true,
  }
  params.SetUnsubscribed(true)

  contact, err := client.Contacts.Update(params)

  // Update by contact email
  params = &resend.UpdateContactRequest{
    Email:        "acme@example.com",
    Unsubscribed: true,
  }
  params.SetUnsubscribed(true)

  contact, err := client.Contacts.Update(params)
  ```

  ```rust Rust theme={null}
  use resend_rs::{types::ContactChanges, Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let changes = ContactChanges::new().with_unsubscribed(true);

    // Update by contact id
    let _contact = resend
      .contacts
      .update("e169aa45-1ecf-4183-9955-b1499d5701d3", changes.clone())
      .await?;

    // Update by contact email
    let _contact = resend
      .contacts
      .update("acme@example.com", changes)
      .await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
      public static void main(String[] args) {
          Resend resend = new Resend("re_xxxxxxxxx");

          // Update by contact id
          UpdateContactOptions params = UpdateContactOptions.builder()
                  .id("e169aa45-1ecf-4183-9955-b1499d5701d3")
                  .unsubscribed(true)
                  .build();

          // Update by contact email
          UpdateContactOptions params = UpdateContactOptions.builder()
                  .email("acme@example.com")
                  .unsubscribed(true)
                  .build();

          UpdateContactResponseSuccess data = resend.contacts().update(params);
      }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  // By Id
  await resend.ContactUpdateAsync(
      contactId: new Guid( "e169aa45-1ecf-4183-9955-b1499d5701d3" ),
      new ContactData()
      {
          FirstName = "Stevie",
          LastName = "Wozniaks",
          IsUnsubscribed = true,
      }
  );

  // By Email
  await resend.ContactUpdateByEmailAsync(
      "acme@example.com",
      new ContactData()
      {
          FirstName = "Stevie",
          LastName = "Wozniaks",
          IsUnsubscribed = true,
      }
  );
  ```

  ```bash cURL theme={null}
  # Update by contact id
  curl -X PATCH 'https://api.resend.com/contacts/520784e2-887d-4c25-b53c-4ad46ad38100' \
       -H 'Authorization: Bearer re_xxxxxxxxx' \
       -H 'Content-Type: application/json' \
       -d $'{
    "unsubscribed": true
  }'

  # Update by contact email
  curl -X PATCH 'https://api.resend.com/contacts/acme@example.com' \
       -H 'Authorization: Bearer re_xxxxxxxxx' \
       -H 'Content-Type: application/json' \
       -d $'{
    "unsubscribed": true
  }'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "object": "contact",
    "id": "479e3145-dd38-476b-932c-529ceb705947"
  }
  ```
</ResponseExample>
