export type IpcSuccess<T> = {
  ok: true;
  data: T;
};

export type IpcFailure = {
  ok: false;
  error: string;
};

export type IpcEnvelope<T> = IpcSuccess<T> | IpcFailure;
