# Create Segment

> Create a new segment for contacts to be added to.

## Body Parameters

<ParamField body="name" type="string" required>
  The name of the segment you want to create.
</ParamField>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.segments.create({
    name: 'Registered Users',
  });
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->segments->create([
    'name' => 'Registered Users',
  ]);
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = 're_xxxxxxxxx'

  params = {
      "name": "Registered Users",
  }

  segment = resend.Segments.create(params)
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  params = {
    name: "Registered Users",
  }
  segment = Resend::Segments.create(params)
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

  	params := &resend.CreateSegmentRequest{
  		Name: "Registered Users",
  	}

  	segment, err := client.Segments.CreateWithContext(ctx, params)
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

    let _segment = resend.segments.create("Registered Users").await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
      public static void main(String[] args) {
          Resend resend = new Resend("re_xxxxxxxxx");

          CreateSegmentOptions options = CreateSegmentOptions.builder()
              .name("Registered Users")
              .build();

          CreateSegmentResponseSuccess response = resend.segments().create(options);
      }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.SegmentCreateAsync( new SegmentData() {
    Name = "Registered Users",
  } );
  Console.WriteLine( "Segment Id={0}", resp.Content );
  ```

  ```bash cURL theme={null}
  curl -X POST 'https://api.resend.com/segments' \
       -H 'Authorization: Bearer re_xxxxxxxxx' \
       -H 'Content-Type: application/json' \
       -d $'{
    "name": "Registered Users"
  }'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "object": "segment",
    "id": "78261eea-8f8b-4381-83c6-79fa7120f1cf",
    "name": "Registered Users"
  }
  ```
</ResponseExample>
