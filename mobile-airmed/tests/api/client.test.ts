import { api } from "../../api/client";

const mockFetch = jest.fn();
global.fetch = mockFetch;

describe("api client", () => {
  beforeEach(() => {
    mockFetch.mockClear();
    jest.resetModules();
  });

  it("makes GET request with correct headers", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ id: 1, name: "test" }),
    });

    const result = await api("/test");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/test"),
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      }),
    );
    expect(result).toEqual({ id: 1, name: "test" });
  });

  it("throws ApiError on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Not found" }),
    });

    await expect(api("/notfound")).rejects.toEqual({
      status: 404,
      detail: "Not found",
    });
  });
});
