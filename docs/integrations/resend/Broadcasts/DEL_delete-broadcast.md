# Delete Broadcast

> Remove an existing broadcast.

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

You can only delete broadcasts that are in the `draft` status. In addition, if you delete a broadcast that has already been scheduled to be sent, we will automatically cancel the scheduled delivery and it won't be sent.

## Path Parameters

<ResendParamField path="broadcast_id" type="string" required>
  The broadcast ID.
</ResendParamField>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.broadcasts.remove(
    '559ac32e-9ef5-46fb-82a1-b76b840c0f7b',
  );
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->broadcasts->remove('559ac32e-9ef5-46fb-82a1-b76b840c0f7b');
  ```

  ```py Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"

  resend.Broadcasts.remove(id="559ac32e-9ef5-46fb-82a1-b76b840c0f7b")
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  Resend::Broadcasts.remove("559ac32e-9ef5-46fb-82a1-b76b840c0f7b")
  ```

  ```go Go theme={null}
  import 	"github.com/resend/resend-go/v3"

  client := resend.NewClient("re_xxxxxxxxx")

  removed, _ := client.Broadcasts.Remove("559ac32e-9ef5-46fb-82a1-b76b840c0f7b")
  ```

  ```rust Rust theme={null}
  use resend_rs::{Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let _deleted = resend
      .broadcasts
      .delete("559ac32e-9ef5-46fb-82a1-b76b840c0f7b")
      .await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  Resend resend = new Resend("re_xxxxxxxxx");

  RemoveBroadcastResponseSuccess data = resend.broadcasts().remove("559ac32e-9ef5-46fb-82a1-b76b840c0f7b");
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  await resend.BroadcastDeleteAsync( new Guid( "559ac32e-9ef5-46fb-82a1-b76b840c0f7b" ) );
  ```

  ```bash cURL theme={null}
  curl -X DELETE 'https://api.resend.com/broadcasts/559ac32e-9ef5-46fb-82a1-b76b840c0f7b' \
       -H 'Authorization: Bearer re_xxxxxxxxx'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "object": "broadcast",
    "id": "559ac32e-9ef5-46fb-82a1-b76b840c0f7b",
    "deleted": true
  }
  ```
</ResponseExample>
