# Delete API key

> Remove an existing API key.

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

<ResendParamField path="api_key_id" type="string" required>
  The API key ID.
</ResendParamField>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.apiKeys.remove(
    'b6d24b8e-af0b-4c3c-be0c-359bbd97381e',
  );
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->apiKeys->remove('b6d24b8e-af0b-4c3c-be0c-359bbd97381e');
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"
  resend.ApiKeys.remove(api_key_id="b6d24b8e-af0b-4c3c-be0c-359bbd97381e")
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  Resend::ApiKeys.remove "b6d24b8e-af0b-4c3c-be0c-359bbd97381e"
  ```

  ```go Go theme={null}
  import 	"github.com/resend/resend-go/v3"

  client := resend.NewClient("re_xxxxxxxxx")
  client.ApiKeys.Remove("b6d24b8e-af0b-4c3c-be0c-359bbd97381e")
  ```

  ```rust Rust theme={null}
  use resend_rs::{Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    resend
      .api_keys
      .delete("b6d24b8e-af0b-4c3c-be0c-359bbd97381e")
      .await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
      public static void main(String[] args) {
          Resend resend = new Resend("re_xxxxxxxxx");

          resend.apiKeys().remove("b6d24b8e-af0b-4c3c-be0c-359bbd97381e");
      }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  await resend.ApiKeyDeleteAsync( new Guid( "b6d24b8e-af0b-4c3c-be0c-359bbd97381e" ) );
  ```

  ```bash cURL theme={null}
  curl -X DELETE 'https://api.resend.com/api-keys/b6d24b8e-af0b-4c3c-be0c-359bbd97381e' \
       -H 'Authorization: Bearer re_xxxxxxxxx'
  ```
</RequestExample>

<ResponseExample>
  ```text Response theme={null}
  HTTP 200 OK
  ```
</ResponseExample>
