# Create Broadcast

> Create a new broadcast to send to your contacts.

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

<ResendParamField body="segment_id" type="string" required>
  The ID of the segment you want to send to.

  <Info>
    Audiences are now called Segments. Follow the [Migration
    Guide](/dashboard/segments/migrating-from-audiences-to-segments).
  </Info>
</ResendParamField>

<ParamField body="from" type="string" required>
  Sender email address.

  To include a friendly name, use the format `"Your Name <sender@domain.com>"`.
</ParamField>

<ParamField body="subject" type="string" required>
  Email subject.
</ParamField>

<ResendParamField body="reply_to" type="string | string[]">
  Reply-to email address. For multiple addresses, send as an array of strings.
</ResendParamField>

<ParamField body="html" type="string">
  The HTML version of the message. You can include Contact Properties in the
  body of the Broadcast. Learn more about [Contact
  Properties](/dashboard/audiences/contacts).
</ParamField>

<ParamField body="text" type="string">
  The plain text version of the message. You can include Contact Properties in the body of the Broadcast. Learn more about [Contact Properties](/dashboard/audiences/contacts).

  <Info>
    If not provided, the HTML will be used to generate a plain text version. You
    can opt out of this behavior by setting value to an empty string.
  </Info>
</ParamField>

<ParamField body="react" type="React.ReactNode">
  The React component used to write the message. *Only available in the Node.js
  SDK.*
</ParamField>

<ParamField body="name" type="string">
  The friendly name of the broadcast. Only used for internal reference.
</ParamField>

<ResendParamField body="topic_id" type="string">
  <TopicBetaBanner />

  The topic ID that the broadcast will be scoped to.
</ResendParamField>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.broadcasts.create({
    segmentId: '78261eea-8f8b-4381-83c6-79fa7120f1cf',
    from: 'Acme <onboarding@resend.dev>',
    subject: 'hello world',
    html: 'Hi {{{FIRST_NAME|there}}}, you can unsubscribe here: {{{RESEND_UNSUBSCRIBE_URL}}}',
  });
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->broadcasts->create([
    'segment_id' => '78261eea-8f8b-4381-83c6-79fa7120f1cf',
    'from' => 'Acme <onboarding@resend.dev>',
    'subject' => 'hello world',
    'html' => 'Hi {{{FIRST_NAME|there}}}, you can unsubscribe here: {{{RESEND_UNSUBSCRIBE_URL}}}',
  ]);
  ```

  ```py Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"

  params: resend.Broadcasts.CreateParams = {
    "segment_id": "78261eea-8f8b-4381-83c6-79fa7120f1cf",
    "from": "Acme <onboarding@resend.dev>",
    "subject": "Hello, world!",
    "html": "Hi {{{FIRST_NAME|there}}}, you can unsubscribe here: {{{RESEND_UNSUBSCRIBE_URL}}}",
  }

  resend.Broadcasts.create(params)
  ```

  ```ruby Ruby theme={null}
  require "resend"

  Resend.api_key = "re_xxxxxxxxx"

  params = {
    "segment_id": "78261eea-8f8b-4381-83c6-79fa7120f1cf",
    "from": "Acme <onboarding@resend.dev>",
    "subject": "hello world",
    "html": "Hi {{{FIRST_NAME|there}}}, you can unsubscribe here: {{{RESEND_UNSUBSCRIBE_URL}}}",
  }
  Resend::Broadcasts.create(params)
  ```

  ```go Go theme={null}
  import "fmt"
  import 	"github.com/resend/resend-go/v3"

  client := resend.NewClient("re_xxxxxxxxx")

  params := &resend.CreateBroadcastRequest{
    SegmentId: "78261eea-8f8b-4381-83c6-79fa7120f1cf",
    From:       "Acme <onboarding@resend.dev>",
    Html:       "Hi {{{FIRST_NAME|there}}}, you can unsubscribe here: {{{RESEND_UNSUBSCRIBE_URL}}}",
    Subject:    "Hello, world!",
  }

  broadcast, _ := client.Broadcasts.Create(params)
  ```

  ```rust Rust theme={null}
  use resend_rs::{types::CreateBroadcastOptions, Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let segment_id = "78261eea-8f8b-4381-83c6-79fa7120f1cf";
    let from = "Acme <onboarding@resend.dev>";
    let subject = "hello world";
    let html = "Hi {{{FIRST_NAME|there}}}, you can unsubscribe here: {{{RESEND_UNSUBSCRIBE_URL}}}";

    let opts = CreateBroadcastOptions::new(segment_id, from, subject).with_html(html);

    let _broadcast = resend.broadcasts.create(opts).await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  Resend resend = new Resend("re_xxxxxxxxx");

  CreateBroadcastOptions params = CreateBroadcastOptions.builder()
      .segmentId("78261eea-8f8b-4381-83c6-79fa7120f1cf")
      .from("Acme <onboarding@resend.dev>")
      .subject("hello world")
      .html("Hi {{{FIRST_NAME|there}}}, you can unsubscribe here: {{{RESEND_UNSUBSCRIBE_URL}}}")
      .build();

  CreateBroadcastResponseSuccess data = resend.broadcasts().create(params);
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.BroadcastAddAsync(
      new BroadcastData()
      {
          DisplayName = "Example Broadcast",
          SegmentId = new Guid( "78261eea-8f8b-4381-83c6-79fa7120f1cf" ),
          From = "Acme <onboarding@resend.dev>",
          Subject = "Hello, world!",
          HtmlBody = "Hi {{{FIRST_NAME|there}}}, you can unsubscribe here: {{{RESEND_UNSUBSCRIBE_URL}}}",
      }
  );
  Console.WriteLine( "Broadcast Id={0}", resp.Content );
  ```

  ```bash cURL theme={null}
  curl -X POST 'https://api.resend.com/broadcasts' \
       -H 'Authorization: Bearer re_xxxxxxxxx' \
       -H 'Content-Type: application/json' \
       -d $'{
    "segment_id": "78261eea-8f8b-4381-83c6-79fa7120f1cf",
    "from": "Acme <onboarding@resend.dev>",
    "subject": "hello world",
    "html": "Hi {{{FIRST_NAME|there}}}, you can unsubscribe here: {{{RESEND_UNSUBSCRIBE_URL}}}"
  }'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "id": "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794"
  }
  ```
</ResponseExample>
