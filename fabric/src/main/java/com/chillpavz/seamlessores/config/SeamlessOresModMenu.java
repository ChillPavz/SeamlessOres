package com.chillpavz.seamlessores.config;

import com.terraformersmc.modmenu.api.ConfigScreenFactory;
import com.terraformersmc.modmenu.api.ModMenuApi;
// NOT AutoConfig: cloth 26.2 moved the screen entry point out to AutoConfigClient, so that the
// server-safe AutoConfig class no longer references GUI types. AutoConfig.getConfigScreen is gone.
import me.shedaniel.autoconfig.AutoConfig;

/**
 * Supplies the config button in Mod Menu's mod list.
 *
 * <p>Mod Menu is optional — it is a {@code compileOnly} dependency and a "suggests" entry in
 * fabric.mod.json. This class is only ever loaded by Mod Menu itself through the {@code modmenu}
 * entrypoint, so nothing here runs when it is absent.
 */
public class SeamlessOresModMenu implements ModMenuApi {

    @Override
    public ConfigScreenFactory<?> getModConfigScreenFactory() {
        return parent -> AutoConfig.getConfigScreen(SeamlessOresConfigData.class, parent).get();
    }
}
