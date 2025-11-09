# List Emails

> Retrieve a list of emails.

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

You can list all emails received by your domain. The list returns references to individual emails. If needed, you can use the `id` of an email to retrieve the email HTML to plain text using the [Retrieve Email](/api-reference/emails/retrieve-email) endpoint.

<QueryParams type="emails" isRequired={true} />

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.emails.list();
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->emails->list();
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"
  resend.Emails.list()
  ```

  ```ruby Ruby theme={null}
  Resend.api_key = "re_xxxxxxxxx"
  emails = Resend::Emails.list
  puts emails
  ```

  ```go Go theme={null}
  import (
    "context"
    "fmt"

    "github.com/resend/resend-go/v3"
  )

  ctx := context.TODO()
  client := resend.NewClient("re_xxxxxxxxx")

  paginatedResp, err := client.Emails.ListWithOptions(ctx, nil)
  if err != nil {
    panic(err)
  }

  fmt.Printf("Found %d emails\n", len(paginatedResp.Data))

  if paginatedResp.HasMore {
    opts := &resend.ListOptions{
      After: &paginatedResp.Data[len(paginatedResp.Data)-1].ID,
    }
    paginatedResp, err = client.Emails.ListWithOptions(ctx, opts)

    if err != nil {
      panic(err)
    }

    fmt.Printf("Found %d more emails in next page\n", len(paginatedResp.Data))
  }
  ```

  ```rust Rust theme={null}
  use resend_rs::{list_opts::ListOptions, Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let _emails = resend.emails.list(ListOptions::default()).await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
      public static void main(String[] args) {
          Resend resend = new Resend("re_xxxxxxxxx");

          ListEmailsResponseSuccess emails = resend.emails().list();
      }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.EmailListAsync();
  Console.WriteLine( "Count={0}", resp.Content.Data.Count );
  ```

  ```bash cURL theme={null}
  curl -X GET 'https://api.resend.com/emails' \
       -H 'Authorization: Bearer re_xxxxxxxxx'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "object": "list",
    "has_more": false,
    "data": [
      {
        "id": "4ef9a417-02e9-4d39-ad75-9611e0fcc33c",
        "to": ["delivered@resend.dev"],
        "from": "Acme <onboarding@resend.dev>",
        "created_at": "2023-04-03T22:13:42.674981+00:00",
        "subject": "Hello World",
        "bcc": null,
        "cc": null,
        "reply_to": null,
        "last_event": "delivered",
        "scheduled_at": null
      },
      {
        "id": "3a9f8c2b-1e5d-4f8a-9c7b-2d6e5f8a9c7b",
        "to": ["user@example.com"],
        "from": "Acme <onboarding@resend.dev>",
        "created_at": "2023-04-03T21:45:12.345678+00:00",
        "subject": "Welcome to Acme",
        "bcc": null,
        "cc": null,
        "reply_to": null,
        "last_event": "opened",
        "scheduled_at": null
      }
    ]
  }
  ```
</ResponseExample>
