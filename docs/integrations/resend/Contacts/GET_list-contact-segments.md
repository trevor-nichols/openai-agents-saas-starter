# List Contact Segments

> Retrieve a list of segments that a contact is part of.

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

<QueryParams type="contacts" isRequired={false} />

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.contacts.segments.list({
    id: 'e169aa45-1ecf-4183-9955-b1499d5701d3',
  });
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->contacts->segments->list(
    contactId: 'e169aa45-1ecf-4183-9955-b1499d5701d3'
  );
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = 're_xxxxxxxxx'

  params = {
      "contact_id": 'e169aa45-1ecf-4183-9955-b1499d5701d3',
  }

  segments = resend.Contacts.Segments.list(params)
  ```

  ```ruby Ruby theme={null}
  require 'resend'

  Resend.api_key = 're_xxxxxxxxx'

  segments = Resend::Contacts::Segments.list(
    contact_id: 'e169aa45-1ecf-4183-9955-b1499d5701d3'
  )
  ```

  ```go Go theme={null}
  package main

  import (
  	"context"
  	"fmt"

  	"github.com/resend/resend-go/v3"
  )

  func main() {
  	ctx := context.TODO()
  	apiKey := "re_xxxxxxxxx"

  	client := resend.NewClient(apiKey)

  	listParams := &resend.ListContactSegmentsRequest{
  		ContactId: "e169aa45-1ecf-4183-9955-b1499d5701d3",
  	}

  	segments, err := client.Contacts.Segments.ListWithContext(ctx, listParams)
  	if err != nil {
  		panic(err)
  	}
  	fmt.Println(segments)
  }
  ```

  ```rust Rust theme={null}
  use resend_rs::{Resend, Result, list_opts::ListOptions};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let _contacts = resend
      .contacts
      .list_contact_segment(
        "e169aa45-1ecf-4183-9955-b1499d5701d3",
        ListOptions::default()
      )
      .await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
    public static void main(String[] args) {
      Resend resend = new Resend("re_xxxxxxxxx");

      resend.contacts().segments().list("e169aa45-1ecf-4183-9955-b1499d5701d3");
    }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.ContactListSegmentsAsync( new Guid( "e169aa45-1ecf-4183-9955-b1499d5701d3" ));
  Console.WriteLine( "Nr Segments={0}", resp.Content.Data.Count );
  ```

  ```bash cURL theme={null}
  curl -X GET 'https://api.resend.com/contacts/e169aa45-1ecf-4183-9955-b1499d5701d3/segments' \
       -H 'Authorization: Bearer re_xxxxxxxxx'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "object": "list",
    "data": [
      {
        "id": "78261eea-8f8b-4381-83c6-79fa7120f1cf",
        "name": "Registered Users",
        "created_at": "2023-10-06T22:59:55.977Z"
      }
    ],
    "has_more": false
  }
  ```
</ResponseExample>
