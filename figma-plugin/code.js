// CLI-Anything Figma Bridge — Plugin code
// Receives commands from the UI (which polls the local relay server)
// and executes them in the Figma canvas.

figma.showUI(__html__, { width: 360, height: 480 });

function hexToRGB(hex) {
  const h = hex.replace("#", "");
  return {
    r: parseInt(h.substring(0, 2), 16) / 255,
    g: parseInt(h.substring(2, 4), 16) / 255,
    b: parseInt(h.substring(4, 6), 16) / 255,
  };
}

function findParent(name) {
  if (!name) return figma.currentPage;
  const node = figma.currentPage.findOne((n) => n.name === name || n.id === name);
  return node || figma.currentPage;
}

async function handleCommand(msg) {
  const { type, params, id } = msg;
  let result = { id, status: "ok" };

  try {
    switch (type) {
      case "CREATE_FRAME": {
        const frame = figma.createFrame();
        frame.name = params.name || "Frame";
        frame.resize(params.width || 400, params.height || 300);
        frame.x = params.x || 0;
        frame.y = params.y || 0;
        if (params.fill) {
          const rgb = hexToRGB(params.fill);
          frame.fills = [{ type: "SOLID", color: rgb }];
        }
        const parent = findParent(params.parent);
        if (parent !== figma.currentPage && "appendChild" in parent) {
          parent.appendChild(frame);
        }
        result.nodeId = frame.id;
        result.name = frame.name;
        break;
      }

      case "CREATE_TEXT": {
        const text = figma.createText();
        await figma.loadFontAsync({
          family: params.fontFamily || "Inter",
          style: "Regular",
        });
        text.characters = params.content || "Text";
        text.fontSize = params.fontSize || 16;
        text.x = params.x || 0;
        text.y = params.y || 0;
        if (params.fill) {
          const rgb = hexToRGB(params.fill);
          text.fills = [{ type: "SOLID", color: rgb }];
        }
        if (params.name) text.name = params.name;
        const textParent = findParent(params.parent);
        if (textParent !== figma.currentPage && "appendChild" in textParent) {
          textParent.appendChild(text);
        }
        result.nodeId = text.id;
        break;
      }

      case "CREATE_RECT": {
        const rect = figma.createRectangle();
        rect.resize(params.width || 100, params.height || 100);
        rect.x = params.x || 0;
        rect.y = params.y || 0;
        if (params.fill) {
          const rgb = hexToRGB(params.fill);
          rect.fills = [{ type: "SOLID", color: rgb }];
        }
        if (params.cornerRadius) {
          rect.cornerRadius = params.cornerRadius;
        }
        if (params.name) rect.name = params.name;
        const rectParent = findParent(params.parent);
        if (rectParent !== figma.currentPage && "appendChild" in rectParent) {
          rectParent.appendChild(rect);
        }
        result.nodeId = rect.id;
        break;
      }

      case "CREATE_ELLIPSE": {
        const ellipse = figma.createEllipse();
        ellipse.resize(params.width || 100, params.height || 100);
        ellipse.x = params.x || 0;
        ellipse.y = params.y || 0;
        if (params.fill) {
          const rgb = hexToRGB(params.fill);
          ellipse.fills = [{ type: "SOLID", color: rgb }];
        }
        if (params.name) ellipse.name = params.name;
        const ellipseParent = findParent(params.parent);
        if (ellipseParent !== figma.currentPage && "appendChild" in ellipseParent) {
          ellipseParent.appendChild(ellipse);
        }
        result.nodeId = ellipse.id;
        break;
      }

      case "CREATE_COMPONENT": {
        const ct = params.componentType;
        if (ct === "button") {
          const frame = figma.createFrame();
          frame.name = params.label || "Button";
          frame.resize(params.width || 160, params.height || 48);
          frame.cornerRadius = params.cornerRadius || 8;
          frame.x = params.x || 0;
          frame.y = params.y || 0;
          const bgColor = hexToRGB(params.bg || "#000000");
          frame.fills = [{ type: "SOLID", color: bgColor }];
          frame.layoutMode = "HORIZONTAL";
          frame.primaryAxisAlignItems = "CENTER";
          frame.counterAxisAlignItems = "CENTER";

          const label = figma.createText();
          await figma.loadFontAsync({ family: "Inter", style: "Semi Bold" });
          label.characters = params.label || "Button";
          label.fontSize = params.fontSize || 16;
          const textColor = hexToRGB(params.textColor || "#FFFFFF");
          label.fills = [{ type: "SOLID", color: textColor }];
          label.fontName = { family: "Inter", style: "Semi Bold" };
          frame.appendChild(label);

          result.nodeId = frame.id;
        } else if (ct === "card") {
          const card = figma.createFrame();
          card.name = params.title || "Card";
          card.resize(params.width || 320, params.height || 200);
          card.cornerRadius = params.cornerRadius || 12;
          card.x = params.x || 0;
          card.y = params.y || 0;
          const cardBg = hexToRGB(params.bg || "#FFFFFF");
          card.fills = [{ type: "SOLID", color: cardBg }];
          card.strokes = [{ type: "SOLID", color: hexToRGB("#E0E0E0") }];
          card.strokeWeight = 1;
          card.layoutMode = "VERTICAL";
          card.paddingTop = 24;
          card.paddingLeft = 24;
          card.paddingRight = 24;
          card.paddingBottom = 24;
          card.itemSpacing = 8;

          if (params.title) {
            const title = figma.createText();
            await figma.loadFontAsync({ family: "Inter", style: "Bold" });
            title.characters = params.title;
            title.fontSize = 20;
            title.fontName = { family: "Inter", style: "Bold" };
            card.appendChild(title);
          }
          if (params.body) {
            const body = figma.createText();
            await figma.loadFontAsync({ family: "Inter", style: "Regular" });
            body.characters = params.body;
            body.fontSize = 14;
            body.fills = [{ type: "SOLID", color: hexToRGB("#666666") }];
            card.appendChild(body);
          }
          result.nodeId = card.id;
        }
        break;
      }

      default:
        result = { id, status: "error", error: `Unknown command: ${type}` };
    }
  } catch (err) {
    result = { id, status: "error", error: String(err) };
  }

  // Send result back to UI to relay to server
  figma.ui.postMessage({ type: "RESULT", payload: result });
}

// Listen for messages from the UI
figma.ui.onMessage = (msg) => {
  if (msg.type === "COMMAND") {
    handleCommand(msg.payload);
  }
};
