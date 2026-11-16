// One shared tooltip for the whole app. Elements opt in with `use:tooltip={{ component, props }}`;
// <TooltipHost /> (mounted once) renders that component next to the hovered or focused element.

/** @typedef {{ component: import('svelte').Component<any>, props?: Record<string, any> }} TipContent */

export const tip = $state({
  open: false,
  /** @type {TipContent | null} */
  content: null,
  /** @type {DOMRect | null} */
  anchor: null,
});

/**
 * @param {HTMLElement} node
 * @param {TipContent | null} content
 */
export function tooltip(node, content) {
  let current = content;
  const show = () => {
    if (!current) return;
    tip.content = current;
    tip.anchor = node.getBoundingClientRect();
    tip.open = true;
  };
  const hide = () => { tip.open = false; };

  node.addEventListener('mouseenter', show);
  node.addEventListener('focus', show);
  node.addEventListener('mouseleave', hide);
  node.addEventListener('blur', hide);

  return {
    /** @param {TipContent | null} next */
    update(next) { current = next; },
    destroy() {
      hide();
      node.removeEventListener('mouseenter', show);
      node.removeEventListener('focus', show);
      node.removeEventListener('mouseleave', hide);
      node.removeEventListener('blur', hide);
    },
  };
}
