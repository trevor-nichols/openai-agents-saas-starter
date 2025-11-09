# Retrieve Email

> Retrieve a single email.

## Path Parameters

<ParamField path="id" type="string" required>
  The Email ID.
</ParamField>

<Info>
  See all available `last_event` types in [the Email Events
  overview](/dashboard/emails/introduction#understand-email-events).
</Info>

<RequestExample>
  ```js Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.emails.get(
    '37e4414c-5e25-4dbc-a071-43552a4bd53b',
  );
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->emails->get('37e4414c-5e25-4dbc-a071-43552a4bd53b');
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"
  resend.Emails.get(email_id="4ef9a417-02e9-4d39-ad75-9611e0fcc33c")
  ```

  ```ruby Ruby theme={null}
  Resend.api_key = "re_xxxxxxxxx"
  email = Resend::Emails.get("4ef9a417-02e9-4d39-ad75-9611e0fcc33c")
  puts email
  ```

  ```go Go theme={null}
  import "github.com/resend/resend-go/v3"

  client := resend.NewClient("re_xxxxxxxxx")

  email, err := client.Emails.Get("4ef9a417-02e9-4d39-ad75-9611e0fcc33c")
  ```

  ```rust Rust theme={null}
  use resend_rs::{Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let _email = resend
      .emails
      .get("4ef9a417-02e9-4d39-ad75-9611e0fcc33c")
      .await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
      public static void main(String[] args) {
          Resend resend = new Resend("re_xxxxxxxxx");

          Email email = resend.emails().get("4ef9a417-02e9-4d39-ad75-9611e0fcc33c");
      }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.EmailRetrieveAsync( new Guid( "4ef9a417-02e9-4d39-ad75-9611e0fcc33c" ) );
  Console.WriteLine( "Subject={0}", resp.Content.Subject );
  ```

  ```bash cURL theme={null}
  curl -X GET 'https://api.resend.com/emails/4ef9a417-02e9-4d39-ad75-9611e0fcc33c' \
       -H 'Authorization: Bearer re_xxxxxxxxx'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "object": "email",
    "id": "4ef9a417-02e9-4d39-ad75-9611e0fcc33c",
    "to": ["delivered@resend.dev"],
    "from": "Acme <onboarding@resend.dev>",
    "created_at": "2023-04-03T22:13:42.674981+00:00",
    "subject": "Hello World",
    "html": "Congrats on sending your <strong>first email</strong>!",
    "text": null,
    "bcc": [],
    "cc": [],
    "reply_to": [],
    "last_event": "delivered",
    "scheduled_at": null
  }
  ```
</ResponseExample>
