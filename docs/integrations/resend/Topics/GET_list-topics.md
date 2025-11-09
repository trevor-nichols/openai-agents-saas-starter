# List Topics

> Retrieve a list of topics for the authenticated user.

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

<QueryParams type="topics" isRequired={true} />

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.topics.list();
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->topics->list();
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"

  resend.Topics.list()
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  Resend::Topics.list()
  ```

  ```go Go theme={null}
  import (
  	"context"

  	"github.com/resend/resend-go/v3"
  )

  func main() {
  	client := resend.NewClient("re_xxxxxxxxx")

  	topics, err := client.Topics.ListWithContext(context.TODO(), nil)
  }
  ```

  ```rust Rust theme={null}
  use resend_rs::{list_opts::ListOptions, Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let _list = resend.topics.list(ListOptions::default()).await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
    public static void main(String[] args) {
      Resend resend = new Resend("re_xxxxxxxxx");

      ListTopicsResponseSuccess response = resend.topics().list();
    }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.TopicListAsync();
  Console.WriteLine( "Nr Topics={0}", resp.Content.Data.Count );
  ```

  ```bash cURL theme={null}
  curl -X GET 'https://api.resend.com/topics' \
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
        "id": "b6d24b8e-af0b-4c3c-be0c-359bbd97381e",
        "name": "Weekly Newsletter",
        "description": "Weekly newsletter for our subscribers",
        "default_subscription": "opt_in",
        "visibility": "public",
        "created_at": "2023-04-08T00:11:13.110779+00:00"
      }
    ]
  }
  ```
</ResponseExample>
