package com.alphintra.auth_service;

import com.alphintra.auth_service.config.SecurityProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

@SpringBootApplication
@EnableConfigurationProperties(SecurityProperties.class)
public class MainApplication {

  private static final Logger log = LoggerFactory.getLogger(MainApplication.class);

  public static void main(String[] args) {
    SpringApplication.run(MainApplication.class, args);
    log.info("Auth service started successfully.");
  }

  @Bean
  public BCryptPasswordEncoder customPasswordEncoder() {
    return new BCryptPasswordEncoder();
  }
}
