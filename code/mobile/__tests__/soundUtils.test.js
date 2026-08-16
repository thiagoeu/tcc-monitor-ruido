import { getColor, getNoiseLabel, getWidth } from "../src/shared/soundUtils";

describe("getColor", () => {
  it("retorna verde para db < 50", () => {
    expect(getColor(0)).toBe("#00E676");
    expect(getColor(49.9)).toBe("#00E676");
  });

  it("retorna amarelo para 50 <= db < 75", () => {
    expect(getColor(50)).toBe("#FFD600");
    expect(getColor(74.9)).toBe("#FFD600");
  });

  it("retorna vermelho para db >= 75", () => {
    expect(getColor(75)).toBe("#FF5252");
    expect(getColor(100)).toBe("#FF5252");
  });
});

describe("getNoiseLabel", () => {
  it("retorna 'Silencioso' para db < 40", () => {
    expect(getNoiseLabel(0)).toBe("Silencioso");
    expect(getNoiseLabel(39.9)).toBe("Silencioso");
  });

  it("retorna 'Moderado' para 40 <= db < 60", () => {
    expect(getNoiseLabel(40)).toBe("Moderado");
    expect(getNoiseLabel(59.9)).toBe("Moderado");
  });

  it("retorna 'Alto' para 60 <= db < 80", () => {
    expect(getNoiseLabel(60)).toBe("Alto");
    expect(getNoiseLabel(79.9)).toBe("Alto");
  });

  it("retorna 'Perigoso' para db >= 80", () => {
    expect(getNoiseLabel(80)).toBe("Perigoso");
    expect(getNoiseLabel(120)).toBe("Perigoso");
  });
});

describe("getWidth", () => {
  it("retorna percentual proporcional", () => {
    expect(getWidth(60)).toBe("50%");
    expect(getWidth(0)).toBe("0%");
  });

  it("limita o percentual em 100%", () => {
    expect(getWidth(120)).toBe("100%");
    expect(getWidth(150)).toBe("100%");
  });
});
