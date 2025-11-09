# List Broadcasts

> Retrieve a list of broadcast.

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

<Info>
  See all available `status` types in [the Broadcasts
  overview](/dashboard/broadcasts/introduction#understand-broadcast-statuses).
</Info>

<QueryParams type="broadcasts" isRequired={false} />

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.broadcasts.list();
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->broadcasts->list();
  ```

  ```py Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"

  resend.Broadcasts.list()
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  Resend::Broadcasts.list()
  ```

  ```go Go theme={null}
  import 	"github.com/resend/resend-go/v3"

  client := resend.NewClient("re_xxxxxxxxx")

  broadcasts, _ := client.Broadcasts.List()
  ```

  ```rust Rust theme={null}
  use resend_rs::{Resend, Result, list_opts::ListOptions};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let _broadcasts = resend.broadcasts.list(ListOptions::default()).await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  Resend resend = new Resend("re_xxxxxxxxx");

  ListBroadcastsResponseSuccess data = resend.broadcasts().list();
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.BroadcastListAsync();
  Console.WriteLine( "Nr Broadcasts={0}", resp.Content.Count );
  ```

  ```bash cURL theme={null}
  curl -X GET 'https://api.resend.com/broadcasts' \
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
        "id": "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794",
        "audience_id": "78261eea-8f8b-4381-83c6-79fa7120f1cf", // now called segment_id
        "segment_id": "78261eea-8f8b-4381-83c6-79fa7120f1cf",
        "status": "draft",
        "created_at": "2024-11-01T15:13:31.723Z",
        "scheduled_at": null,
        "sent_at": null,
        "topic_id": "b6d24b8e-af0b-4c3c-be0c-359bbd97381e"
      },
      {
        "id": "559ac32e-9ef5-46fb-82a1-b76b840c0f7b",
        "audience_id": "78261eea-8f8b-4381-83c6-79fa7120f1cf", // now called segment_id
        "segment_id": "78261eea-8f8b-4381-83c6-79fa7120f1cf",
        "status": "sent",
        "created_at": "2024-12-01T19:32:22.980Z",
        "scheduled_at": "2024-12-02T19:32:22.980Z",
        "sent_at": "2024-12-02T19:32:22.980Z",
        "topic_id": "b6d24b8e-af0b-4c3c-be0c-359bbd97381e"
      }
    ]
  }
  ```
</ResponseExample>
