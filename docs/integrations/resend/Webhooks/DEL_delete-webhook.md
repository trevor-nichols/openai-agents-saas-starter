# Delete Webhook

> Remove an existing webhook.

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

<ResendParamField path="webhook_id" type="string" required>
  The Webhook ID.
</ResendParamField>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.webhooks.remove(
    '4dd369bc-aa82-4ff3-97de-514ae3000ee0',
  );
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->webhooks->remove('4dd369bc-aa82-4ff3-97de-514ae3000ee0');
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = 're_xxxxxxxxx'

  webhook = resend.Webhooks.remove(webhook_id='4dd369bc-aa82-4ff3-97de-514ae3000ee0')
  ```

  ```ruby Ruby theme={null}
  require 'resend'

  Resend.api_key = 're_xxxxxxxxx'

  webhook = Resend::Webhooks.remove('4dd369bc-aa82-4ff3-97de-514ae3000ee0')
  ```

  ```go Go theme={null}
  import "github.com/resend/resend-go/v3"

  client := resend.NewClient("re_xxxxxxxxx")

  webhook, err := client.Webhooks.Remove("4dd369bc-aa82-4ff3-97de-514ae3000ee0")
  ```

  ```rust Rust theme={null}
  use resend_rs::{Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let _deleted = resend
      .webhooks
      .delete("4dd369bc-aa82-4ff3-97de-514ae3000ee0")
      .await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
      public static void main(String[] args) {
          Resend resend = new Resend("re_xxxxxxxxx");

          RemoveWebhookResponseSuccess response = resend.webhooks().remove("4dd369bc-aa82-4ff3-97de-514ae3000ee0");
      }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  await resend.WebhookDeleteAsync( new Guid( "d91cd9bd-1176-453e-8fc1-35364d380206" ) );
  ```

  ```bash cURL theme={null}
  curl -X DELETE 'https://api.resend.com/webhooks/4dd369bc-aa82-4ff3-97de-514ae3000ee0' \
       -H 'Authorization: Bearer re_xxxxxxxxx'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "object": "webhook",
    "id": "4dd369bc-aa82-4ff3-97de-514ae3000ee0",
    "deleted": true
  }
  ```
</ResponseExample>
