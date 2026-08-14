package com.chillpavz.seamlessores.platform;

import com.chillpavz.seamlessores.platform.services.IPlatformHelper;
import net.neoforged.fml.ModList;
import net.neoforged.fml.loading.FMLLoader;

public class NeoForgePlatformHelper implements IPlatformHelper {

    @Override
    public String getPlatformName() {

        return "NeoForge";
    }

    @Override
    public boolean isModLoaded(String modId) {

        return ModList.get().isLoaded(modId);
    }

    @Override
    public boolean isDevelopmentEnvironment() {

        // FMLLoader.isProduction() is a STATIC method at NeoForge 21.4 (FML 6) but an INSTANCE method
        // reached via FMLLoader.getCurrent() at 21.10 (FML 10) - a binary break inside this branch's
        // 1.21.4 to 1.21.10 range. Resolve it reflectively so one jar spans both. This only labels a
        // startup log line, so assume production if neither shape is present rather than crash.
        try {
            java.lang.reflect.Method m = FMLLoader.class.getMethod("isProduction");
            Object target = java.lang.reflect.Modifier.isStatic(m.getModifiers())
                    ? null
                    : FMLLoader.class.getMethod("getCurrent").invoke(null);
            return !((Boolean) m.invoke(target));
        } catch (Throwable t) {
            return false;
        }
    }
}
