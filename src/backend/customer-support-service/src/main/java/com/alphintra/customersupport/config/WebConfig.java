package com.alphintra.customersupport.config;

import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Bean
    public FilterRegistrationBean<AgentEndpointFilter> agentEndpointFilter() {
        FilterRegistrationBean<AgentEndpointFilter> registration = new FilterRegistrationBean<>();
        registration.setFilter(new AgentEndpointFilter());
        registration.addUrlPatterns("/agents");
        registration.setOrder(1); // High priority
        return registration;
    }
}