package org.myau.shaya.ide.debug.model;

import org.eclipse.debug.core.DebugException;
import org.eclipse.debug.core.model.IValue;
import org.eclipse.debug.core.model.IVariable;

/**
 * Значение переменной ALG (скаляр или структура с детьми).
 */
public class ShayaValue extends ShayaDebugElement implements IValue {

	private String text;
	private final IVariable[] children;

	public ShayaValue(ShayaDebugTarget target, String text) {
		this(target, text, null);
	}

	public ShayaValue(ShayaDebugTarget target, String text, IVariable[] children) {
		super(target, target.getLaunch());
		this.text = text == null ? "null" : text;
		this.children = children == null ? new IVariable[0] : children;
	}

	void updateText(String text) {
		this.text = text == null ? "null" : text;
	}

	@Override
	public String getReferenceTypeName() {
		return "ALG";
	}

	@Override
	public String getValueString() {
		return text;
	}

	@Override
	public boolean isAllocated() {
		return true;
	}

	@Override
	public IVariable[] getVariables() {
		return children;
	}

	@Override
	public boolean hasVariables() {
		return children.length > 0;
	}
}
