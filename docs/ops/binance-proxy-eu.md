EU egress proxy for Binance (Testnet)

Summary
- This guide sets up a small HTTPS egress proxy in Europe and configures `trading-engine` to route Binance API calls through it.
- Note: Bypassing geo-restrictions may violate Binance ToS. Prefer moving workloads to an EU region when possible.

Option A — Compute Engine VM + Squid (recommended)
1) Reserve a static IP (EU):
   - `gcloud compute addresses create binance-proxy-eu --region europe-west1`
   - `gcloud compute addresses describe binance-proxy-eu --region europe-west1 --format='get(address)'`

2) Create a small Debian VM in `europe-west1` using that address (e2-micro is enough), open TCP 3128 only from your cluster egress IP(s):
   - `gcloud compute instances create eu-proxy-1 --zone europe-west1-b --machine-type e2-micro --address binance-proxy-eu --tags squid-proxy`
   - `gcloud compute firewall-rules create allow-squid-from-cluster --allow tcp:3128 --target-tags squid-proxy --source-ranges=<US_CLUSTER_NAT_IP/32>`

3) Install and configure Squid with basic auth:
   - `gcloud compute ssh eu-proxy-1 --zone europe-west1-b`
   - `sudo apt-get update && sudo apt-get install -y squid apache2-utils`
   - `sudo htpasswd -c /etc/squid/passwords trader`  # set a strong password
   - Edit `/etc/squid/squid.conf` and add (near top):
     - `auth_param basic program /usr/lib/squid/basic_ncsa_auth /etc/squid/passwords`
     - `auth_param basic realm proxy`
     - `acl authenticated proxy_auth REQUIRED`
     - `http_access allow authenticated`
     - Ensure `http_port 3128` is present
     - Optionally restrict to Binance hosts only: `acl binance dstdomain .binance.com testnet.binance.vision` and `http_access allow authenticated binance`
   - `sudo systemctl restart squid && sudo systemctl enable squid`

4) Test from your cluster/pod:
   - `kubectl run -it curl --image=curlimages/curl --rm --restart=Never -- env HTTPS_PROXY=http://trader:<PASS>@<EU_PROXY_IP>:3128 curl https://api.ipify.org`
   - The IP should match `binance-proxy-eu` address.

5) Configure the trading-engine Deployment:
   - Create a namespace-scoped secret (no credentials in Git):
     - `kubectl -n trading create secret generic binance-proxy --from-literal=HTTPS_PROXY=http://trader:<PASS>@<EU_PROXY_IP>:3128`
   - Ensure `BINANCE_API_ENABLED=true` and `BINANCE_TESTNET_ENABLED=true`.
   - Apply the kustomize overlay.

Notes
- The app now reads `HTTPS_PROXY`/`HTTP_PROXY` to route:
  - Java 11+ HttpClient calls (time, account, orders)
  - XChange (Binance) client via ExchangeSpecification proxy settings
- Check logs for: `Outbound HTTP proxy enabled` and `Applied HTTP proxy to XChange`.
- To bypass the proxy for internal traffic, set `NO_PROXY` in the same secret (e.g., `10.0.0.0/8,*.svc,localhost`).

Alternative: Istio egress in EU (advanced)
- Run a minimal EU GKE cluster and add an Istio EgressGateway with SNI to `testnet.binance.vision`.
- Route US cluster traffic through an EU egress gateway over mTLS or a public gateway. More complex and not covered here.

Cloud Run caveat
- Running a CONNECT proxy on Cloud Run requires TLS termination and HTTPS-proxy semantics; common proxies (tinyproxy/squid) expect plaintext HTTP from clients and are not ideal behind Cloud Run’s HTTPS-only ingress.
  A Compute Engine VM is simpler and more reliable for this use case.

