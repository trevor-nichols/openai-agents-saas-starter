# Update Domain

> Update an existing domain.

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

<ResendParamField path="domain_id" type="string" required>
  The Domain ID.
</ResendParamField>

## Body Parameters

<ResendParamField body="click_tracking" type="boolean">
  Track clicks within the body of each HTML email.
</ResendParamField>

<ResendParamField body="open_tracking" type="boolean">
  Track the open rate of each email.
</ResendParamField>

<ParamField body="tls" type="string" default="opportunistic">
  <ul>
    <li>
      `opportunistic`: Opportunistic TLS means that it always attempts to make a
      secure connection to the receiving mail server. If it can't establish a
      secure connection, it sends the message unencrypted.
    </li>

    <li>
      `enforced`: Enforced TLS on the other hand, requires that the email
      communication must use TLS no matter what. If the receiving server does
      not support TLS, the email will not be sent.
    </li>
  </ul>
</ParamField>

<RequestExample>
  ```ts Node.js theme={null}
  import { Resend } from 'resend';

  const resend = new Resend('re_xxxxxxxxx');

  const { data, error } = await resend.domains.update({
    id: 'b8617ad3-b712-41d9-81a0-f7c3d879314e',
    openTracking: false,
    clickTracking: true,
    tls: 'enforced',
  });
  ```

  ```php PHP theme={null}
  $resend = Resend::client('re_xxxxxxxxx');

  $resend->domains->update(
    'b8617ad3-b712-41d9-81a0-f7c3d879314e',
    [
      'open_tracking' => false,
      'click_tracking' => true,
      'tls' => 'enforced',
    ]
  );
  ```

  ```python Python theme={null}
  import resend

  resend.api_key = "re_xxxxxxxxx"

  params: resend.Domains.UpdateParams = {
    "id": "b8617ad3-b712-41d9-81a0-f7c3d879314e",
    "open_tracking": False,
    "click_tracking": True,
    "tls": "enforced",
  }

  resend.Domains.update(params)
  ```

  ```ruby Ruby theme={null}
  Resend.api_key = "re_xxxxxxxxx"

  Resend::Domains.update({
    id: "b8617ad3-b712-41d9-81a0-f7c3d879314e",
    open_tracking: false,
    click_tracking: true,
    tls: "enforced",
  })
  ```

  ```go Go theme={null}
  import 	"github.com/resend/resend-go/v3"

  client := resend.NewClient("re_xxxxxxxxx")

  updateDomainParams := &resend.UpdateDomainRequest{
    OpenTracking:  false,
    ClickTracking: true,
    Tls: resend.Enforced,
  }

  updated, err := client.Domains.Update("b8617ad3-b712-41d9-81a0-f7c3d879314e", updateDomainParams)
  ```

  ```rust Rust theme={null}
  use resend_rs::{types::{DomainChanges, Tls}, Resend, Result};

  #[tokio::main]
  async fn main() -> Result<()> {
    let resend = Resend::new("re_xxxxxxxxx");

    let changes = DomainChanges::new()
      .with_open_tracking(false)
      .with_click_tracking(true)
      .with_tls(Tls::Enforced);

    let _domain = resend
      .domains
      .update("b8617ad3-b712-41d9-81a0-f7c3d879314e", changes)
      .await?;

    Ok(())
  }
  ```

  ```java Java theme={null}
  Resend resend = new Resend("re_xxxxxxxxx");

  UpdateDomainOptions params = UpdateDomainOptions.builder()
                  .id("b8617ad3-b712-41d9-81a0-f7c3d879314e")
                  .openTracking(false)
                  .clickTracking(true)
                  .tls(Tls.ENFORCED)
                  .build();

  resend.domains().update(params);
  ```

  ```csharp .NET theme={null}
  using Resend;

  IResend resend = ResendClient.Create( "re_xxxxxxxxx" ); // Or from DI

  await resend.DomainUpdateAsync(
      new Guid( "b8617ad3-b712-41d9-81a0-f7c3d879314e" ),
      new DomainUpdateData()
      {
          TrackOpen = false,
          TrackClicks = true,
          TlsMode = TlsMode.Enforced,
      }
  );
  ```

  ```bash cURL theme={null}
  curl -X PATCH 'https://api.resend.com/domains/b8617ad3-b712-41d9-81a0-f7c3d879314e' \
       -H 'Authorization: Bearer re_xxxxxxxxx' \
       -H 'Content-Type: application/json' \
       -d $'{
    "open_tracking": false,
    "click_tracking": true,
    "tls": "enforced"
  }'
  ```
</RequestExample>

<ResponseExample>
  ```json Response theme={null}
  {
    "object": "domain",
    "id": "b8617ad3-b712-41d9-81a0-f7c3d879314e"
  }
  ```
</ResponseExample>
