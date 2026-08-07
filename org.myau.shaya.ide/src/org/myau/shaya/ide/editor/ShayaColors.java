package org.myau.shaya.ide.editor;

import org.eclipse.swt.graphics.RGB;

/** Syntax colour palette (light theme defaults). */
public final class ShayaColors {

	private ShayaColors() {
	}

	public static final RGB DEFAULT = new RGB(30, 30, 30);
	public static final RGB KEYWORD = new RGB(0, 80, 120);
	public static final RGB TYPE = new RGB(0, 100, 60);
	public static final RGB BUILTIN = new RGB(120, 70, 20);
	public static final RGB STRING = new RGB(160, 60, 20);
	public static final RGB COMMENT = new RGB(90, 110, 90);
	public static final RGB NUMBER = new RGB(140, 40, 40);
}
