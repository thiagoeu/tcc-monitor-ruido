import {
  getSensores,
  enviarMedicao,
  ocuparAmbiente,
  liberarAmbiente,
  heartbeatSessao,
} from "../src/services/api";

const API_BASE_URL = "http://teste.local:5000";

const mockFetch = (response, ok = true) => {
  global.fetch = jest.fn().mockResolvedValue({
    ok,
    json: async () => response,
  });
};

describe("getSensores", () => {
  beforeEach(() => {
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("retorna a lista de sensores em caso de sucesso", async () => {
    const sensores = [{ id: 1, nome: "Sala 1" }];
    mockFetch(sensores);

    const result = await getSensores();

    expect(global.fetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/api/ambientes?ativo=1`,
      { headers: { "bypass-tunnel-reminder": "true" } },
    );
    expect(result).toEqual(sensores);
  });

  it("retorna [] quando a resposta não é ok", async () => {
    mockFetch({ erro: "Erro ao buscar sensores" }, false);

    const result = await getSensores();

    expect(result).toEqual([]);
  });

  it("retorna [] em caso de falha de rede", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("Network error"));

    const result = await getSensores();

    expect(result).toEqual([]);
  });
});

describe("enviarMedicao", () => {
  beforeEach(() => {
    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("envia medição com db arredondado em 2 casas", async () => {
    const data = { ok: true };
    mockFetch(data);

    await enviarMedicao(1, 55.555);

    expect(global.fetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/medicoes`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "bypass-tunnel-reminder": "true",
      },
      body: JSON.stringify({ sensor_id: 1, db: 55.55 }),
    });
  });

  it("não lança erro quando a resposta não é ok", async () => {
    mockFetch({ erro: "Erro no servidor" }, false);

    await expect(enviarMedicao(1, 50)).resolves.toBeUndefined();
  });
});

describe("ocuparAmbiente", () => {
  beforeEach(() => {
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("retorna dados em caso de sucesso", async () => {
    const data = { ok: true };
    mockFetch(data);

    const result = await ocuparAmbiente(1, "device-1");

    expect(global.fetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/sessoes`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "bypass-tunnel-reminder": "true",
      },
      body: JSON.stringify({ sensor_id: 1, device_id: "device-1" }),
    });
    expect(result).toEqual(data);
  });

  it("lança erro em caso de conflito (409)", async () => {
    mockFetch({ erro: "Ambiente ocupado" }, false);

    await expect(ocuparAmbiente(1, "device-1")).rejects.toThrow(
      "Ambiente ocupado",
    );
  });
});

describe("liberarAmbiente", () => {
  beforeEach(() => {
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("chama DELETE com URL codificada", async () => {
    mockFetch({});

    await liberarAmbiente("sensor/1", "device-1");

    expect(global.fetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/api/sessoes/sensor%2F1`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "bypass-tunnel-reminder": "true",
        },
        body: JSON.stringify({ device_id: "device-1" }),
      },
    );
  });

  it("não lança erro em caso de falha", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("Network error"));

    await expect(liberarAmbiente(1, "device-1")).resolves.toBeUndefined();
  });
});

describe("heartbeatSessao", () => {
  beforeEach(() => {
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("chama PUT com URL codificada", async () => {
    mockFetch({});

    await heartbeatSessao("sensor/1", "device-1");

    expect(global.fetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/api/sessoes/sensor%2F1/heartbeat`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "bypass-tunnel-reminder": "true",
        },
        body: JSON.stringify({ device_id: "device-1" }),
      },
    );
  });

  it("não lança erro em caso de falha", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("Network error"));

    await expect(heartbeatSessao(1, "device-1")).resolves.toBeUndefined();
  });
});
