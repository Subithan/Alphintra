package com.alphintra.trading_engine.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

import java.net.*;
import java.net.http.HttpClient;
import java.time.Duration;
import java.util.Optional;

@Configuration
public class AppConfig {

    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }

    @Bean
    public ProxySettings proxySettings() {
        String httpsProxy = System.getenv("HTTPS_PROXY");
        String httpProxy = System.getenv("HTTP_PROXY");
        String proxy = (httpsProxy != null && !httpsProxy.isBlank()) ? httpsProxy : httpProxy;

        if (proxy == null || proxy.isBlank()) {
            return ProxySettings.disabled();
        }

        try {
            // Accept formats like http://user:pass@host:port or http://host:port
            URI uri = URI.create(proxy);
            String host = uri.getHost();
            int port = (uri.getPort() > 0) ? uri.getPort() : 80;
            String userInfo = uri.getUserInfo();
            String username = null;
            String password = null;
            if (userInfo != null && !userInfo.isBlank()) {
                int idx = userInfo.indexOf(':');
                if (idx >= 0) {
                    username = userInfo.substring(0, idx);
                    password = userInfo.substring(idx + 1);
                } else {
                    username = userInfo;
                }
            }
            return ProxySettings.enabled(host, port, username, password);
        } catch (Exception e) {
            System.err.println("⚠️ Invalid proxy URL in HTTPS_PROXY/HTTP_PROXY: " + e.getMessage());
            return ProxySettings.disabled();
        }
    }

    @Bean
    public HttpClient httpClient(ProxySettings proxySettings) {
        HttpClient.Builder builder = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(15))
                // Proxies and CONNECT typically rely on HTTP/1.1
                .version(HttpClient.Version.HTTP_1_1);

        if (proxySettings.isEnabled()) {
            builder.proxy(ProxySelector.of(new InetSocketAddress(proxySettings.getHost(), proxySettings.getPort())));

            if (proxySettings.getUsername() != null && !proxySettings.getUsername().isBlank()) {
                final String proxyUser = proxySettings.getUsername();
                final String proxyPass = Optional.ofNullable(proxySettings.getPassword()).orElse("");
                builder.authenticator(new Authenticator() {
                    @Override
                    protected PasswordAuthentication getPasswordAuthentication() {
                        if (getRequestorType() == RequestorType.PROXY) {
                            return new PasswordAuthentication(proxyUser, proxyPass.toCharArray());
                        }
                        return null;
                    }
                });
            }

            System.out.println("🌍 Outbound HTTP proxy enabled: " + proxySettings.getHost() + ":" + proxySettings.getPort());
        } else {
            System.out.println("🌍 Outbound HTTP proxy disabled");
        }

        return builder.build();
    }
}
