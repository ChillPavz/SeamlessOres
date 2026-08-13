package com.chillpavz.seamlessores.config;

import com.terraformersmc.modmenu.api.ConfigScreenFactory;
import com.terraformersmc.modmenu.api.ModMenuApi;

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
        return SeamlessOresConfigScreenFactory::create;
    }
}
