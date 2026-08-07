package org.myau.shaya.ide;

import org.eclipse.jface.resource.ImageDescriptor;
import org.eclipse.ui.plugin.AbstractUIPlugin;
import org.osgi.framework.BundleContext;

/**
 * Activator for org.myau.shaya.ide — ALG IDE / SCHOOLALGOL (.alg).
 */
public class Activator extends AbstractUIPlugin {

	public static final String PLUGIN_ID = "org.myau.shaya.ide";

	private static Activator plugin;

	@Override
	public void start(BundleContext context) throws Exception {
		super.start(context);
		plugin = this;
		org.myau.shaya.ide.run.ShayaLastLaunch.load();
	}

	@Override
	public void stop(BundleContext context) throws Exception {
		try {
			org.myau.shaya.ide.run.ShayaLastLaunch.save();
		} catch (Exception ignored) {
		}
		plugin = null;
		super.stop(context);
	}

	public static Activator getDefault() {
		return plugin;
	}

	public static ImageDescriptor getImageDescriptor(String path) {
		return imageDescriptorFromPlugin(PLUGIN_ID, path);
	}

	/** Persist dialog settings (Recent / Run Last). */
	public void persistDialogSettings() {
		saveDialogSettings();
	}
}
