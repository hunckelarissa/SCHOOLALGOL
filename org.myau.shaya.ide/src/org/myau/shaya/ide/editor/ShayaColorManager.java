package org.myau.shaya.ide.editor;

import java.util.HashMap;
import java.util.Map;

import org.eclipse.swt.graphics.Color;
import org.eclipse.swt.graphics.RGB;
import org.eclipse.swt.widgets.Display;

public class ShayaColorManager {

	private final Map<RGB, Color> colors = new HashMap<>();

	public Color getColor(RGB rgb) {
		Color c = colors.get(rgb);
		if (c == null) {
			c = new Color(Display.getCurrent(), rgb);
			colors.put(rgb, c);
		}
		return c;
	}

	public void dispose() {
		for (Color c : colors.values()) {
			c.dispose();
		}
		colors.clear();
	}
}
