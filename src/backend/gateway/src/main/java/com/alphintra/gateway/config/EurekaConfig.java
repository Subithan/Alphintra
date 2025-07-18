package com.alphintra.gateway.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.cloud.netflix.eureka.server.EnableEurekaServer;

@Configuration
@EnableEurekaServer
@Profile("eureka-server")
public class EurekaConfig {
}