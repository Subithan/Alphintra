package com.alphintra.trading_engine.config;

public class ProxySettings {
    private final boolean enabled;
    private final String host;
    private final int port;
    private final String username;
    private final String password;

    private ProxySettings(boolean enabled, String host, int port, String username, String password) {
        this.enabled = enabled;
        this.host = host;
        this.port = port;
        this.username = username;
        this.password = password;
    }

    public static ProxySettings disabled() {
        return new ProxySettings(false, null, -1, null, null);
    }

    public static ProxySettings enabled(String host, int port, String username, String password) {
        return new ProxySettings(true, host, port, username, password);
    }

    public boolean isEnabled() {
        return enabled;
    }

    public String getHost() {
        return host;
    }

    public int getPort() {
        return port;
    }

    public String getUsername() {
        return username;
    }

    public String getPassword() {
        return password;
    }
}

