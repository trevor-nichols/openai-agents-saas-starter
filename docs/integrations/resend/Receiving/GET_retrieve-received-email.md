# Retrieve Received Email

> Retrieve a single received email.

## Path Parameters

<ParamField path="id" type="string" required>
  The ID for the received email.
</ParamField>

<RequestExample>
  ```js Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.emails.receiving.get(
    '37e4414c-5e25-4dbc-a071-43552a4bd53b',
  );
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->emails->receiving->get('37e4414c-5e25-4dbc-a071-43552a4bd53b');
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"

  resend.Emails.Receiving.get(email_id="37e4414c-5e25-4dbc-a071-43552a4bd53b")
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  Resend::Emails::Receiving.get("37e4414c-5e25-4dbc-a071-43552a4bd53b")
  ```

  ```go Go theme={null}
  import (
  	"context"

  	"github.com/resend/resend-go/v3"
  )

  func main() {
  	client := resend.NewClient("re_xxxxxxxxx")

  	email, err := client.Emails.Receiving.GetWithContext(
  		context.TODO(),
  		"37e4414c-5e25-4dbc-a071-43552a4bd53b",
  	)
  }
  ```

  ```rust Rust theme={null}
  use resend_rs::{Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let _email = resend
      .receiving
      .get("37e4414c-5e25-4dbc-a071-43552a4bd53b")
      .await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
    public static void main(String[] args) {
      Resend resend = new Resend("re_xxxxxxxxx");

      ReceivedEmail email = resend.receiving().get("37e4414c-5e25-4dbc-a071-43552a4bd53b");
    }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.ReceivedEmailRetrieveAsync( new Guid( "4ef9a417-02e9-4d39-ad75-9611e0fcc33c" ) );
  Console.WriteLine( "Subject={0}", resp.Content.Subject );
  ```

  ```bash cURL theme={null}
  curl -X GET 'https://api.resend.com/emails/receiving/4ef9a417-02e9-4d39-ad75-9611e0fcc33c' \
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
    "headers": {
      "return-path": "lucas.costa@resend.com",
      "mime-version": "1.0"
    },
    "bcc": [],
    "cc": [],
    "reply_to": [],
    "message_id": "<example+123>",
    "attachments": [
      {
        "id": "2a0c9ce0-3112-4728-976e-47ddcd16a318",
        "filename": "avatar.png",
        "content_type": "image/png",
        "content_disposition": "inline",
        "content_id": "img001"
      }
    ]
  }
  ```
</ResponseExample>
