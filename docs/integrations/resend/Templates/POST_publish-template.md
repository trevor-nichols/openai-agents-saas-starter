# Publish Template

> Publish a template.

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

<ParamField body="id | alias" type="string">
  The ID or alias of the template to publish.
</ParamField>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.templates.publish(
    '34a080c9-b17d-4187-ad80-5af20266e535',
  );
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->templates->publish('34a080c9-b17d-4187-ad80-5af20266e535');
  ```

  ```py Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"

  resend.Templates.publish("34a080c9-b17d-4187-ad80-5af20266e535")
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  Resend::Templates.publish("34a080c9-b17d-4187-ad80-5af20266e535")
  ```

  ```go Go theme={null}
  import (
  	"context"

  	"github.com/resend/resend-go/v3"
  )

  func main() {
  	client := resend.NewClient("re_xxxxxxxxx")

  	template, err := client.Templates.PublishWithContext(
  		context.TODO(),
  		"34a080c9-b17d-4187-ad80-5af20266e535",
  	)
  }
  ```

  ```rust Rust theme={null}
  use resend_rs::{Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let _published = resend
      .templates
      .publish("34a080c9-b17d-4187-ad80-5af20266e535")
      .await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
      public static void main(String[] args) {
          Resend resend = new Resend("re_xxxxxxxxx");

          PublishTemplateResponseSuccess data = resend.templates().publish("34a080c9-b17d-4187-ad80-5af20266e535");
      }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  await resend.TemplatePublishAsync( new Guid( "34a080c9-b17d-4187-ad80-5af20266e535" ) );
  ```

  ```bash cURL theme={null}
  curl -X POST 'https://api.resend.com/templates/34a080c9-b17d-4187-ad80-5af20266e535/publish' \
       -H 'Authorization: Bearer re_xxxxxxxxx' \
       -H 'Content-Type: application/json'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "id": "34a080c9-b17d-4187-ad80-5af20266e535",
    "object": "template"
  }
  ```
</ResponseExample>
