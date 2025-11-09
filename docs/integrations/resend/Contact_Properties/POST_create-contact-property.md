# Create Contact Property

> Create a custom property for your contacts.

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

## Body Parameters

<ResendParamField body="key" type="string" required>
  The property key. Max length is `50` characters. Only alphanumeric characters
  and underscores are allowed.
</ResendParamField>

<ResendParamField body="type" type="string" required>
  The property type. Possible values: `string` or `number`.
</ResendParamField>

<ResendParamField body="fallback_value" type="string | number">
  The default value to use when the property is not set for a contact. Must
  match the type specified in the `type` field.
</ResendParamField>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.contactProperties.create({
    key: 'company_name',
    type: 'string',
    fallbackValue: 'Acme Corp',
  });
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->contactProperties->create([
    'key' => 'company_name',
    'type' => 'string',
    'fallback_value' => 'Acme Corp',
  ]);
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = 're_xxxxxxxxx'

  params = {
      "key": "company_name",
      "type": "string",
      "fallback_value": "Acme Corp",
  }

  contact_property = resend.ContactProperties.create(params)
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  property = Resend::ContactProperties.create({
    key: "company_name",
    type: "string",
    fallback_value: "Acme Corp"
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

  	params := &resend.CreateContactPropertyRequest{
  		Key:           "company_name",
  		Type:          "string",
  		FallbackValue: "Acme Corp",
  	}

  	property, err := client.ContactProperties.CreateWithContext(ctx, params)
  	if err != nil {
  		panic(err)
  	}
  	fmt.Println(property)
  }
  ```

  ```rust Rust theme={null}
  use resend_rs::{
    types::{CreateContactPropertyOptions, PropertyType},
    Resend, Result,
  };

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let contact_property = CreateContactPropertyOptions::new("company_name", PropertyType::String)
      .with_fallback("Acme Corp");

    let _contact_property = resend.contacts.create_property(contact_property).await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
    public static void main(String[] args) {
      Resend resend = new Resend("re_xxxxxxxxx");

      CreateContactPropertyOptions options = CreateContactPropertyOptions.builder()
        .key("company_name")
        .type("string")
        .fallbackValue("Acme Corp")
        .build();

      resend.contactProperties().create(options);
    }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.ContactPropCreateAsync( new ContactPropertyData() {
    Key = "company_name",
    PropertyType = ContactPropertyType.String,
    DefaultValue = "Acme Corp",
  } );
  Console.WriteLine( "Prop Id={0}", resp.Content );
  ```

  ```bash cURL theme={null}
  curl -X POST 'https://api.resend.com/contact-properties' \
       -H 'Authorization: Bearer re_xxxxxxxxx' \
       -H 'Content-Type: application/json' \
       -d $'{
    "key": "company_name",
    "type": "string",
    "fallback_value": "Acme Corp"
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
