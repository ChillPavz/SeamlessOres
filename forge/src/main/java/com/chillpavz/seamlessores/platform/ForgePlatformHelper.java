package com.chillpavz.seamlessores.platform;

import com.chillpavz.seamlessores.platform.services.IPlatformHelper;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.fml.loading.FMLLoader;

public class ForgePlatformHelper implements IPlatformHelper {

    @Override
    public String getPlatformName() {

        return "Forge";
    }

    @Override
    public boolean isModLoaded(String modId) {

        return ModList.get().isLoaded(modId);
    }

    @Override
    public boolean isDevelopmentEnvironment() {

        // Classic Forge kept the static form; NeoForge 26.x moved to FMLLoader.getCurrent().isProduction().
        return !FMLLoader.isProduction();
    }
}
