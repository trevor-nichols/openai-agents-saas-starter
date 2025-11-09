# Create Domain

> Create a domain through the Resend Email API.

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

<ParamField body="name" type="string" required>
  The name of the domain you want to create.
</ParamField>

<ParamField body="region" type="string" default="us-east-1">
  The region where emails will be sent from. Possible values: `'us-east-1' |
    'eu-west-1' | 'sa-east-1' | 'ap-northeast-1'`
</ParamField>

<ResendParamField body="custom_return_path" type="string" default="send">
  For advanced use cases, choose a subdomain for the Return-Path address. The
  custom return path is used for SPF authentication, DMARC alignment, and
  handling bounced emails. Defaults to `send` (i.e., `send.yourdomain.tld`). Avoid
  setting values that could undermine credibility (e.g. `testing`), as they may
  be exposed to recipients.

  Learn more about [custom return paths](/dashboard/domains/introduction#custom-return-path).
</ResendParamField>

<Info>
  See all available `status` types in [the Domains
  overview](/dashboard/domains/introduction#understand-a-domain-status).
</Info>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.domains.create({ name: 'example.com' });
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->domains->create([
    'name' => 'example.com'
  ]);
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"

  params: resend.Domains.CreateParams = {
    "name": "example.com",
  }

  resend.Domains.create(params)
  ```

  ```ruby Ruby theme={null}
  Resend.api_key = ENV["RESEND_API_KEY"]

  params = {
    name: "example.com",
  }
  domain = Resend::Domains.create(params)
  puts domain
  ```

  ```go Go theme={null}
  import 	"github.com/resend/resend-go/v3"

  client := resend.NewClient("re_xxxxxxxxx")

  params := &resend.CreateDomainRequest{
      Name: "example.com",
  }

  domain, err := client.Domains.Create(params)
  ```

  ```rust Rust theme={null}
  use resend_rs::{types::CreateDomainOptions, Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let _domain = resend
      .domains
      .add(CreateDomainOptions::new("example.com"))
      .await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  import com.resend.*;

  public class Main {
      public static void main(String[] args) {
          Resend resend = new Resend("re_xxxxxxxxx");

          CreateDomainOptions params = CreateDomainOptions
                  .builder()
                  .name("example.com").build();

          CreateDomainResponse domain = resend.domains().create(params);
      }
  }
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  var resp = await resend.DomainAddAsync( "example.com" );
  Console.WriteLine( "Domain Id={0}", resp.Content.Id );
  ```

  ```bash cURL theme={null}
  curl -X POST 'https://api.resend.com/domains' \
       -H 'Authorization: Bearer re_xxxxxxxxx' \
       -H 'Content-Type: application/json' \
       -d $'{
    "name": "example.com"
  }'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "id": "4dd369bc-aa82-4ff3-97de-514ae3000ee0",
    "name": "example.com",
    "created_at": "2023-03-28T17:12:02.059593+00:00",
    "status": "not_started",
    "records": [
      {
        "record": "SPF",
        "name": "send",
        "type": "MX",
        "ttl": "Auto",
        "status": "not_started",
        "value": "feedback-smtp.us-east-1.amazonses.com",
        "priority": 10
      },
      {
        "record": "SPF",
        "name": "send",
        "value": "\"v=spf1 include:amazonses.com ~all\"",
        "type": "TXT",
        "ttl": "Auto",
        "status": "not_started"
      },
      {
        "record": "DKIM",
        "name": "nhapbbryle57yxg3fbjytyodgbt2kyyg._domainkey",
        "value": "nhapbbryle57yxg3fbjytyodgbt2kyyg.dkim.amazonses.com.",
        "type": "CNAME",
        "status": "not_started",
        "ttl": "Auto"
      },
      {
        "record": "DKIM",
        "name": "xbakwbe5fcscrhzshpap6kbxesf6pfgn._domainkey",
        "value": "xbakwbe5fcscrhzshpap6kbxesf6pfgn.dkim.amazonses.com.",
        "type": "CNAME",
        "status": "not_started",
        "ttl": "Auto"
      },
      {
        "record": "DKIM",
        "name": "txrcreso3dqbvcve45tqyosxwaegvhgn._domainkey",
        "value": "txrcreso3dqbvcve45tqyosxwaegvhgn.dkim.amazonses.com.",
        "type": "CNAME",
        "status": "not_started",
        "ttl": "Auto"
      }
    ],
    "region": "us-east-1"
  }
  ```
</ResponseExample>
