import { Slider, HStack, Text, NumberInput, Box, Separator } from '@chakra-ui/react'
import type { ParamDef } from '../schemas/params'

interface ParamSliderProps {
  param: ParamDef
  value: number
  onChange: (key: string, value: number) => void
  disabled?: boolean
}

export function ParamSlider({ param, value, onChange, disabled }: ParamSliderProps) {
  // 判断是否是 Kd 参数，在其前面加分隔线
  const isKd = param.key === 'kd'

  return (
    <Box>
      {isKd && <Separator mb={3} opacity={0.5} />}
      <HStack gap={2.5} w="full">
        <Text
          fontSize="xs"
          fontWeight="medium"
          color="fg"
          minW="52px"
          textAlign="right"
          flexShrink={0}
        >
          {param.label}
        </Text>

        <Box flex={1}>
          <Slider.Root
            min={param.min}
            max={param.max}
            step={param.step}
            value={[value]}
            disabled={disabled}
            onValueChange={(d) => onChange(param.key, d.value[0])}
            size="sm"
            colorPalette="brand"
          >
            <Slider.Control>
              <Slider.Track bg="gray.100">
                <Slider.Range />
              </Slider.Track>
              <Slider.Thumbs />
            </Slider.Control>
          </Slider.Root>
        </Box>

        <NumberInput.Root
          min={param.min}
          max={param.max}
          step={param.step}
          value={String(value)}
          disabled={disabled}
          onValueChange={(d) => {
            const v = parseFloat(d.value)
            if (!isNaN(v)) onChange(param.key, v)
          }}
          size="xs"
          w="78px"
          flexShrink={0}
        >
          <NumberInput.Input
            textAlign="right"
            fontFamily="mono"
            fontSize="xs"
            borderRadius="md"
            borderColor="gray.200"
            _focus={{ borderColor: 'brand.500', boxShadow: '0 0 0 1px {colors.brand.500}' }}
          />
        </NumberInput.Root>

        <Text fontSize="xs" color="fg.muted" minW="44px" flexShrink={0}>
          {param.unit || ''}
        </Text>
      </HStack>
    </Box>
  )
}
