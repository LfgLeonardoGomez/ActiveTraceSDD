import { useState, useId } from 'react';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { Spinner } from '@/shared/components/ui/Spinner';
import { Input } from '@/shared/components/ui/Input';
import { Button } from '@/shared/components/ui/Button';
import { useCrearConvocatoria } from '../../hooks/useColoquios';
import type { ConvocatoriaDia } from '../../types/coloquios.types';

const step1Schema = z.object({
  materia_id: z.string().min(1, 'Seleccioná una materia'),
  cohorte_id: z.string().min(1, 'Seleccioná un cohorte'),
  instancia: z.coerce.number().int().min(1, 'La instancia debe ser al menos 1'),
  titulo: z.string().min(1, 'El título es requerido'),
});

const step2Schema = z.object({
  dias: z
    .array(
      z.object({
        fecha: z.string().min(1, 'La fecha es requerida'),
        cupo_maximo: z.coerce.number().int().min(1, 'El cupo debe ser al menos 1'),
      }),
    )
    .min(1, 'Agregá al menos un día con cupos'),
});

interface Step1Data {
  materia_id: string;
  cohorte_id: string;
  instancia: number;
  titulo: string;
}

interface Step2Data {
  dias: ConvocatoriaDia[];
}

type FormData = Step1Data & Step2Data;

interface ConvocatoriaFormProps {
  onSuccess?: () => void;
}

export function ConvocatoriaForm({ onSuccess }: ConvocatoriaFormProps) {
  const formId = useId();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [step1, setStep1] = useState<Step1Data>({
    materia_id: '',
    cohorte_id: '',
    instancia: 1,
    titulo: '',
  });
  const [step2, setStep2] = useState<Step2Data>({ dias: [{ fecha: '', cupo_maximo: 30 }] });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { mutate: crear, isPending } = useCrearConvocatoria();

  const validateStep1 = () => {
    const result = step1Schema.safeParse(step1);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      result.error.errors.forEach((e) => {
        fieldErrors[e.path[0] as string] = e.message;
      });
      setErrors(fieldErrors);
      return false;
    }
    setErrors({});
    return true;
  };

  const validateStep2 = () => {
    const result = step2Schema.safeParse(step2);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      result.error.errors.forEach((e) => {
        if (e.path.length === 2) {
          fieldErrors[`dias_${e.path[1]}_${e.path[0]}`] = e.message;
        } else {
          fieldErrors.dias = e.message;
        }
      });
      setErrors(fieldErrors);
      return false;
    }
    setErrors({});
    return true;
  };

  const handleNext = () => {
    if (step === 1 && validateStep1()) setStep(2);
    else if (step === 2 && validateStep2()) setStep(3);
  };

  const handleBack = () => {
    if (step > 1) setStep((s) => s - 1);
  };

  const handleAddDia = () => {
    setStep2((prev) => ({
      dias: [...prev.dias, { fecha: '', cupo_maximo: 30 }],
    }));
  };

  const handleRemoveDia = (idx: number) => {
    setStep2((prev) => ({
      dias: prev.dias.filter((_, i) => i !== idx),
    }));
  };

  const handleDiaChange = (idx: number, field: keyof ConvocatoriaDia, value: string) => {
    setStep2((prev) => ({
      dias: prev.dias.map((d, i) =>
        i === idx ? { ...d, [field]: field === 'cupo_maximo' ? Number(value) : value } : d,
      ),
    }));
  };

  const handleSubmit = () => {
    crear(
      {
        ...step1,
        ...step2,
      } as any,
      {
        onSuccess: (data) => {
          if (onSuccess) onSuccess();
          navigate(`/coordinacion/coloquios/${data.id}`);
        },
        onError: () => {
          setStep(3);
        },
      },
    );
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-2">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center gap-2">
            <span
              className={`flex size-8 items-center justify-center rounded-full text-sm font-medium ${
                s === step
                  ? 'bg-primary-600 text-white'
                  : s < step
                    ? 'bg-success-100 text-success-700'
                    : 'bg-neutral-100 text-neutral-400'
              }`}
            >
              {s < step ? '✓' : s}
            </span>
            <span className={`text-sm ${s === step ? 'font-medium text-neutral-900' : 'text-neutral-500'}`}>
              {s === 1 ? 'Datos generales' : s === 2 ? 'Días y cupos' : 'Confirmar'}
            </span>
          </div>
        ))}
      </div>

      {step === 1 && (
        <div className="space-y-4 rounded-lg border border-neutral-200 bg-white p-6">
          <h3 className="text-base font-semibold text-neutral-900">Datos generales</h3>

          <Input
            id={`${formId}-materia`}
            label="Materia"
            value={step1.materia_id}
            onChange={(e) => setStep1((p) => ({ ...p, materia_id: e.target.value }))}
            placeholder="ID de la materia"
            error={errors.materia_id}
          />

          <Input
            id={`${formId}-cohorte`}
            label="Cohorte"
            value={step1.cohorte_id}
            onChange={(e) => setStep1((p) => ({ ...p, cohorte_id: e.target.value }))}
            placeholder="ID del cohorte"
            error={errors.cohorte_id}
          />

          <Input
            id={`${formId}-instancia`}
            label="Instancia"
            type="number"
            min={1}
            value={step1.instancia}
            onChange={(e) => setStep1((p) => ({ ...p, instancia: Number(e.target.value) }))}
            error={errors.instancia}
          />

          <Input
            id={`${formId}-titulo`}
            label="Título"
            value={step1.titulo}
            onChange={(e) => setStep1((p) => ({ ...p, titulo: e.target.value }))}
            error={errors.titulo}
          />
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4 rounded-lg border border-neutral-200 bg-white p-6">
          <h3 className="text-base font-semibold text-neutral-900">Días y cupos</h3>

          {errors.dias && (
            <p className="text-sm text-danger-600">{errors.dias}</p>
          )}

          <div className="space-y-3">
            {step2.dias.map((dia, idx) => (
              <div key={idx} className="flex items-end gap-3 rounded-md border border-neutral-200 p-3">
                <div className="flex-1">
                  <Input
                    label="Fecha"
                    type="date"
                    value={dia.fecha}
                    onChange={(e) => handleDiaChange(idx, 'fecha', e.target.value)}
                  />
                </div>
                <div className="w-32">
                  <Input
                    label="Cupo máximo"
                    type="number"
                    min={1}
                    value={dia.cupo_maximo}
                    onChange={(e) => handleDiaChange(idx, 'cupo_maximo', e.target.value)}
                  />
                </div>
                {step2.dias.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveDia(idx)}
                    className="mb-0.5 rounded-md p-2 text-neutral-400 hover:bg-danger-50 hover:text-danger-600"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={handleAddDia}
            className="text-sm font-medium text-primary-600 hover:underline"
          >
            + Agregar día
          </button>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4 rounded-lg border border-neutral-200 bg-white p-6">
          <h3 className="text-base font-semibold text-neutral-900">Confirmar convocatoria</h3>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between border-b border-neutral-100 pb-2">
              <span className="text-neutral-500">Materia</span>
              <span className="font-medium text-neutral-900">{step1.materia_id}</span>
            </div>
            <div className="flex justify-between border-b border-neutral-100 pb-2">
              <span className="text-neutral-500">Cohorte</span>
              <span className="font-medium text-neutral-900">{step1.cohorte_id}</span>
            </div>
            <div className="flex justify-between border-b border-neutral-100 pb-2">
              <span className="text-neutral-500">Instancia</span>
              <span className="font-medium text-neutral-900">{step1.instancia}</span>
            </div>
            <div className="flex justify-between border-b border-neutral-100 pb-2">
              <span className="text-neutral-500">Título</span>
              <span className="font-medium text-neutral-900">{step1.titulo}</span>
            </div>
            <div className="flex justify-between border-b border-neutral-100 pb-2">
              <span className="text-neutral-500">Días</span>
              <span className="font-medium text-neutral-900">{step2.dias.length}</span>
            </div>
            {step2.dias.map((d, i) => (
              <div key={i} className="flex justify-between pl-4 text-xs text-neutral-600">
                <span>{d.fecha}</span>
                <span>Cupo: {d.cupo_maximo}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={step === 1 || isPending}
        >
          Anterior
        </Button>

        {step < 3 ? (
          <Button onClick={handleNext}>Siguiente</Button>
        ) : (
          <Button onClick={handleSubmit} isLoading={isPending}>
            {isPending ? 'Creando convocatoria...' : 'Confirmar'}
          </Button>
        )}
      </div>
    </div>
  );
}
