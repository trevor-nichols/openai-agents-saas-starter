# Retrieve Segment

> Retrieve a single segment.

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

<ResendParamField path="segment_id" type="string" required>
  The Segment ID.
</ResendParamField>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.segments.get(
    '78261eea-8f8b-4381-83c6-79fa7120f1cf',
  );
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->segments->get('78261eea-8f8b-4381-83c6-79fa7120f1cf');
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = 're_xxxxxxxxx'

  segment = resend.Segments.get('78261eea-8f8b-4381-83c6-79fa7120f1cf')
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  segment = Resend::Segments.get("78261eea-8f8b-4381-83c6-79fa7120f1cf")
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

  	segment, err := client.Segments.GetWithContext(ctx, "78261eea-8f8b-4381-83c6-79fa7120f1cf")
  	if err != nil {
  		panic(err)
  	}
  	fmt.Println(segment)
  }
  ```

  ```rust Rust theme={null}
  use resend_rs::{Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let _segment = resend
      .segments
      .get("78261eea-8f8b-4381-83c6-79fa7120f1cf")
      .await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
      public static void main(String[] args) {
          Resend resend = new Resend("re_xxxxxxxxx");

          GetSegmentResponseSuccess response = resend.segments().get("78261eea-8f8b-4381-83c6-79fa7120f1cf");
      }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.SegmentRetrieveAsync( new Guid( "b6d24b8e-af0b-4c3c-be0c-359bbd97381e" ) );
  Console.WriteLine( "Segment Id={0}", resp.Content.Id );
  ```

  ```bash cURL theme={null}
  curl -X GET 'https://api.resend.com/segments/78261eea-8f8b-4381-83c6-79fa7120f1cf' \
       -H 'Authorization: Bearer re_xxxxxxxxx'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "object": "segment",
    "id": "78261eea-8f8b-4381-83c6-79fa7120f1cf",
    "name": "Registered Users",
    "created_at": "2023-10-06T22:59:55.977Z"
  }
  ```
</ResponseExample>
