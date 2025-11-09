# Update Contact Property

> Update an existing contact property.

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

<ResendParamField path="contact_property_id" type="string" required>
  The Contact Property ID.
</ResendParamField>

<Note>
  The `key` and `type` fields cannot be changed after creation. This preserves
  data integrity for existing contact values.
</Note>

## Body Parameters

<ResendParamField body="fallback_value" type="string | number">
  The default value to use when the property is not set for a contact. Must
  match the type of the property.
</ResendParamField>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.contactProperties.update({
    id: 'b6d24b8e-af0b-4c3c-be0c-359bbd97381e',
    fallbackValue: 'Example Company',
  });
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->contactProperties->update('b6d24b8e-af0b-4c3c-be0c-359bbd97381', [
    'fallback_value' => 'Example Company',
  ]);
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = 're_xxxxxxxxx'

  params = {
      "id": "b6d24b8e-af0b-4c3c-be0c-359bbd97381e",
      "fallback_value": "Example Company",
  }

  contact_property = resend.ContactProperties.update(params)
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  property = Resend::ContactProperties.update({
    id: "b6d24b8e-af0b-4c3c-be0c-359bbd97381e",
    fallback_value: "Example Company"
  })
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

  	params := &resend.UpdateContactPropertyRequest{
  		Id:            "b6d24b8e-af0b-4c3c-be0c-359bbd97381e",
  		FallbackValue: "Example Company",
  	}

  	property, err := client.ContactProperties.UpdateWithContext(ctx, params)
  	if err != nil {
  		panic(err)
  	}
  	fmt.Println(property)
  }
  ```

  ```rust Rust theme={null}
  use resend_rs::{types::ContactPropertyChanges, Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let update = ContactPropertyChanges::default().with_fallback("Example Company");
    let _contact_property = resend
      .contacts
      .update_property("b6d24b8e-af0b-4c3c-be0c-359bbd97381e", update)
      .await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
    public static void main(String[] args) {
      Resend resend = new Resend("re_xxxxxxxxx");

      UpdateContactPropertyOptions options = UpdateContactPropertyOptions.builder()
        .id("b6d24b8e-af0b-4c3c-be0c-359bbd97381e")
        .fallbackValue("Example Company")
        .build();

      resend.contactProperties().update(options);
    }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.ContactPropUpdateAsync(
    new Guid( "b6d24b8e-af0b-4c3c-be0c-359bbd97381e" ),
    new ContactPropertyUpdateData() {
      DefaultValue = "Example Company",
    }
  );
  ```

  ```bash cURL theme={null}
  curl -X PATCH 'https://api.resend.com/contact-properties/b6d24b8e-af0b-4c3c-be0c-359bbd97381e' \
       -H 'Authorization: Bearer re_xxxxxxxxx' \
       -H 'Content-Type: application/json' \
       -d $'{
    "fallback_value": "Example Company"
  }'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "object": "contact_property",
    "id": "b6d24b8e-af0b-4c3c-be0c-359bbd97381e"
  }
  ```
</ResponseExample>
