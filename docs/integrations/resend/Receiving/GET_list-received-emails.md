# List Received Emails

> Retrieve a list of received emails for the authenticated user.

export const QueryParams = ({type, isRequired}) => {
  return <>
      <h2>Query Parameters</h2>

      {isRequired ? <ParamField query="limit" type="number">
          Number of {type} to retrieve.
          <ul>
            <li>
              Default value: <code>20</code>
            </li>
            <li>
              Maximum value: <code>100</code>
            </li>
            <li>
              Minimum value: <code>1</code>
            </li>
          </ul>
        </ParamField> : <>
          <p>
            Note that the <code>limit</code> parameter is <em>optional</em>. If
            you do not provide a <code>limit</code>, all {type} will be returned
            in a single response.
          </p>
          <ParamField query="limit" type="number">
            Number of {type} to retrieve.
            <ul>
              <li>
                Maximum value: <code>100</code>
              </li>
              <li>
                Minimum value: <code>1</code>
              </li>
            </ul>
          </ParamField>
        </>}

      <ParamField query="after" type="string">
        The ID <em>after</em> which we'll retrieve more {type} (for pagination).
        This ID will <em>not</em> be included in the returned list. Cannot be
        used with the
        <code>before</code> parameter.
      </ParamField>
      <ParamField query="before" type="string">
        The ID <em>before</em> which we'll retrieve more {type} (for
        pagination). This ID will <em>not</em> be included in the returned list.
        Cannot be used with the <code>after</code> parameter.
      </ParamField>
      <Info>
        You can only use either <code>after</code> or <code>before</code>{' '}
        parameter, not both. See our{' '}
        <a href="/api-reference/pagination">pagination guide</a> for more
        information.
      </Info>
    </>;
};

<QueryParams type="emails" isRequired={false} />

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.emails.receiving.list();
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->emails->receiving->list();
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"

  resend.Emails.Receiving.list()
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  Resend::Emails::Receiving.list()
  ```

  ```go Go theme={null}
  import (
  	"context"

  	"github.com/resend/resend-go/v3"
  )

  func main() {
  	client := resend.NewClient("re_xxxxxxxxx")

  	emails, err := client.Emails.Receiving.ListWithContext(context.TODO())
  }
  ```

  ```rust Rust theme={null}
  use resend_rs::{list_opts::ListOptions, Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let _email = resend.receiving.list(ListOptions::default()).await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
    public static void main(String[] args) {
      Resend resend = new Resend("re_xxxxxxxxx");

      ListReceivedEmailsResponse response = resend.receiving().list();
    }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.ReceivedEmailListAsync();
  Console.WriteLine( "Nr Received={0}", resp.Content.Data.Count );
  ```

  ```bash cURL theme={null}
  curl -X GET 'https://api.resend.com/emails/receiving' \
       -H 'Authorization: Bearer re_xxxxxxxxx'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "object": "list",
    "has_more": true,
    "data": [
      {
        "id": "a39999a6-88e3-48b1-888b-beaabcde1b33",
        "to": ["recipient@example.com"],
        "from": "sender@example.com",
        "created_at": "2025-10-09 14:37:40.951732+00",
        "subject": "Hello World",
        "bcc": [],
        "cc": [],
        "reply_to": [],
        "message_id": "<111-222-333@email.provider.example.com>",
        "attachments": [
          {
            "filename": "example.txt",
            "content_type": "text/plain",
            "content_id": null,
            "content_disposition": "attachment",
            "id": "47e999c7-c89c-4999-bf32-aaaaa1c3ff21",
            "size": 13
          }
        ]
      }
    ]
  }
  ```
</ResponseExample>
