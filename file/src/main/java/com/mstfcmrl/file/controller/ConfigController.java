package com.mstfcmrl.file.controller;

import com.mstfcmrl.file.model.Config;
import com.mstfcmrl.file.service.ConfigService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/config")
public class ConfigController {

    private final ConfigService configService;

    public ConfigController(ConfigService configService) {
        this.configService = configService;
    }

    @GetMapping
    public Config getConfig() {
        return configService.getConfig();
    }
}
