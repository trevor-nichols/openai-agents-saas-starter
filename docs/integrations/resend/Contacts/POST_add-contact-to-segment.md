# Add Contact to Segment

> Add an existing contact to a segment.

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

<SegmentsBetaBanner />

## Path Parameters

Either `id` or `email` must be provided.

<ParamField path="id" type="string">
  The Contact ID.
</ParamField>

<ParamField path="email" type="string">
  The Contact Email.
</ParamField>

<ResendParamField path="segment_id" type="string" required>
  The Segment ID.
</ResendParamField>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  // Add by contact id
  const { data, error } = await resend.contacts.segments.add({
    id: 'e169aa45-1ecf-4183-9955-b1499d5701d3',
    segmentId: '78261eea-8f8b-4381-83c6-79fa7120f1cf',
  });

  // Add by contact email
  const { data, error } = await resend.contacts.segments.add({
    email: 'steve.wozniak@gmail.com',
    segmentId: '78261eea-8f8b-4381-83c6-79fa7120f1cf',
  });
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  // Add by contact id
  $resend->contacts->segments->add(
    contact: 'e169aa45-1ecf-4183-9955-b1499d5701d3',
    segmentId: '78261eea-8f8b-4381-83c6-79fa7120f1cf'
  );

  // Add by contact email
  $resend->contacts->segments->add(
    contact: 'steve.wozniak@gmail.com',
    segmentId: '78261eea-8f8b-4381-83c6-79fa7120f1cf'
  );
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = 're_xxxxxxxxx'

  # Add by contact id
  params = {
      "segment_id": '78261eea-8f8b-4381-83c6-79fa7120f1cf',
      "contact_id": 'e169aa45-1ecf-4183-9955-b1499d5701d3',
  }

  response = resend.Contacts.Segments.add(params)
  ```

  ```ruby Ruby theme={null}
  require 'resend'

  Resend.api_key = 're_xxxxxxxxx'

  # Add by contact id
  result = Resend::Contacts::Segments.add(
    contact_id: 'e169aa45-1ecf-4183-9955-b1499d5701d3',
    segment_id: '78261eea-8f8b-4381-83c6-79fa7120f1cf'
  )

  # Add by contact email
  result = Resend::Contacts::Segments.add(
    email: 'steve.wozniak@gmail.com',
    segment_id: '78261eea-8f8b-4381-83c6-79fa7120f1cf'
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

  	// Add by contact id
  	addParams := &resend.AddContactSegmentRequest{
  		ContactId: "e169aa45-1ecf-4183-9955-b1499d5701d3",
  		SegmentId: "78261eea-8f8b-4381-83c6-79fa7120f1cf",
  	}

  	response, err := client.Contacts.Segments.AddWithContext(ctx, addParams)
  	if err != nil {
  		panic(err)
  	}
  	fmt.Println(response)

  	// Add by contact email
  	addByEmailParams := &resend.AddContactSegmentRequest{
  		Email:     "steve.wozniak@gmail.com",
  		SegmentId: "78261eea-8f8b-4381-83c6-79fa7120f1cf",
  	}

  	response, err = client.Contacts.Segments.AddWithContext(ctx, addByEmailParams)
  	if err != nil {
  		panic(err)
  	}
  	fmt.Println(response)
  }
  ```

  ```rust Rust theme={null}
  use resend_rs::{Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    // Update by contact id
    let _contact = resend
      .contacts
      .add_contact_segment(
        "e169aa45-1ecf-4183-9955-b1499d5701d3",
        "78261eea-8f8b-4381-83c6-79fa7120f1cf",
      )
      .await?;

    // // Update by contact email
    let _contact = resend
      .contacts
      .add_contact_segment(
        "steve.wozniak@gmail.com",
        "78261eea-8f8b-4381-83c6-79fa7120f1cf",
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

      // Add by contact id
      AddContactToSegmentOptions optionsById = AddContactToSegmentOptions.builder()
        .id("e169aa45-1ecf-4183-9955-b1499d5701d3")
        .segmentId("78261eea-8f8b-4381-83c6-79fa7120f1cf")
        .build();

      resend.contacts().segments().add(optionsById);

      // Add by contact email
      AddContactToSegmentOptions optionsByEmail = AddContactToSegmentOptions.builder()
        .email("steve.wozniak@gmail.com")
        .segmentId("78261eea-8f8b-4381-83c6-79fa7120f1cf")
        .build();

      resend.contacts().segments().add(optionsByEmail);
    }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  await resend.ContactAddToSegmentAsync(
      contactId: new Guid( "e169aa45-1ecf-4183-9955-b1499d5701d3" ),
      segmentId: new Guid( "78261eea-8f8b-4381-83c6-79fa7120f1cf" )
  );
  ```

  ```bash cURL theme={null}
  // Update by contact id
  curl -X POST 'https://api.resend.com/contacts/e169aa45-1ecf-4183-9955-b1499d5701d3/segments/78261eea-8f8b-4381-83c6-79fa7120f1cf' \
       -H 'Authorization: Bearer re_xxxxxxxxx'

  // Update by contact email
  curl -X POST 'https://api.resend.com/contacts/steve.wozniak@gmail.com/segments/78261eea-8f8b-4381-83c6-79fa7120f1cf' \
       -H 'Authorization: Bearer re_xxxxxxxxx' \
       -H 'Content-Type: application/json'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "id": "78261eea-8f8b-4381-83c6-79fa7120f1cf"
  }
  ```
</ResponseExample>
