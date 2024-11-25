package com.mstfcmrl.file.service;

import com.mstfcmrl.file.model.Config;
import com.squareup.moshi.JsonAdapter;
import com.squareup.moshi.Moshi;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.InitializingBean;

import java.io.FileReader;
import java.io.IOException;
import java.nio.file.*;
import java.util.concurrent.atomic.AtomicReference;

@Service
public class ConfigService implements InitializingBean {

    private static final String CONFIG_FILE_PATH = System.getenv("CONFIG_FILE_PATH");
    private final AtomicReference<Config> configCache = new AtomicReference<>();

    @Override
    public void afterPropertiesSet() throws Exception {
        loadConfig();
        watchConfigFile();
    }

    public Config getConfig() {
        return configCache.get();
    }

    private void loadConfig() {
        Moshi moshi = new Moshi.Builder().build();
        JsonAdapter<Config> jsonAdapter = moshi.adapter(Config.class);
        try (FileReader reader = new FileReader(CONFIG_FILE_PATH)) {
            Config config = jsonAdapter.fromJson(com.squareup.moshi.JsonReader.of(okio.Okio.buffer(okio.Okio.source(Paths.get(CONFIG_FILE_PATH).toFile()))));
            configCache.set(config);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void watchConfigFile() {
        Path configDir = Paths.get(CONFIG_FILE_PATH).getParent();
        try {
            WatchService watchService = FileSystems.getDefault().newWatchService();
            configDir.register(watchService, StandardWatchEventKinds.ENTRY_MODIFY);

            Thread watcherThread = new Thread(() -> {
                try {
                    while (true) {
                        WatchKey key = watchService.take();
                        for (WatchEvent<?> event : key.pollEvents()) {
                            WatchEvent.Kind<?> kind = event.kind();
                            Path fileName = (Path) event.context();

                            if (kind == StandardWatchEventKinds.ENTRY_MODIFY && fileName.toString().equals(Paths.get(CONFIG_FILE_PATH).getFileName().toString())) {
                                System.out.println("Configuration file updated, reloading...");
                                loadConfig();
                            }
                        }
                        key.reset();
                    }
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            });

            watcherThread.setDaemon(true);
            watcherThread.start();

        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
